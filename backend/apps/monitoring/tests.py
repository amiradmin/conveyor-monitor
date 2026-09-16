from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from django.conf import settings

from .models import Alarm, Conveyor, TelemetrySample


class MonitoringApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="operator", password="test-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.conveyor = Conveyor.objects.create(code="CV-01", name="Conveyor CV-01")

    def test_status_uses_fresh_persisted_telemetry(self) -> None:
        TelemetrySample.objects.create(
            conveyor=self.conveyor,
            speed_mps=2.4,
            alignment_offset_mm=12.0,
            volume_m3h=100.0,
            tear_probability=0.1,
            confidence=0.91,
        )

        response = self.client.get("/api/conveyors/CV-01/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["conveyor"], "CV-01")
        self.assertEqual(response.data["state"], "RUNNING")
        self.assertEqual(response.data["telemetry_source"], "database")
        self.assertAlmostEqual(response.data["mass_flow_tph"], 132.0)
        self.assertAlmostEqual(response.data["load_percent"], 22.0)
        self.assertEqual(response.data["alignment_status"], "NORMAL")
        self.assertEqual(response.data["tear_status"], "NORMAL")

    def test_internal_ingest_requires_service_token_and_creates_alarms(self) -> None:
        unauthenticated = APIClient()
        payload = {
            "conveyor_id": "CV-01",
            "belt_speed_mps": 2.3,
            "alignment_offset_mm": 30.0,
            "volume_m3h": 500.0,
            "tear_probability": 0.5,
            "confidence": 0.95,
        }

        denied = unauthenticated.post("/api/telemetry/ingest/", payload, format="json")
        self.assertEqual(denied.status_code, 403)

        accepted = unauthenticated.post(
            "/api/telemetry/ingest/",
            payload,
            format="json",
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_SERVICE_TOKEN,
        )
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(TelemetrySample.objects.count(), 1)
        self.assertTrue(Alarm.objects.filter(code="ALIGNMENT_WARNING").exists())
        self.assertTrue(Alarm.objects.filter(code="TEAR_WARNING").exists())
        self.assertTrue(Alarm.objects.filter(code="OVERLOAD_CRITICAL").exists())

    def test_alarm_can_be_acknowledged(self) -> None:
        alarm = Alarm.objects.create(
            conveyor=self.conveyor,
            code="ALIGNMENT_WARNING",
            severity=Alarm.Severity.WARNING,
            message="Alignment warning",
        )

        response = self.client.post(f"/api/events/{alarm.id}/acknowledge/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        alarm.refresh_from_db()
        self.assertTrue(alarm.acknowledged)

    def test_events_can_filter_acknowledged_state(self) -> None:
        Alarm.objects.create(
            conveyor=self.conveyor,
            code="A1",
            severity=Alarm.Severity.INFO,
            message="one",
            acknowledged=False,
        )
        Alarm.objects.create(
            conveyor=self.conveyor,
            code="A2",
            severity=Alarm.Severity.INFO,
            message="two",
            acknowledged=True,
        )

        response = self.client.get("/api/events/?conveyor=CV-01&acknowledged=false")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "A1")
