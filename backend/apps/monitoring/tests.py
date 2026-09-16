from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Alarm, Conveyor, TelemetrySample


@override_settings(EVIDENCE_CAPTURE_ENABLED=False)
class MonitoringApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="operator", password="test-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.internal_client = APIClient()
        self.conveyor = Conveyor.objects.create(code="CV-01", name="Conveyor CV-01")

    def _ingest(self, **overrides):
        payload = {
            "conveyor_id": "CV-01",
            "belt_speed_mps": 2.3,
            "alignment_offset_mm": 0.0,
            "volume_m3h": 100.0,
            "tear_probability": 0.01,
            "confidence": 0.95,
        }
        payload.update(overrides)
        return self.internal_client.post(
            "/api/telemetry/ingest/",
            payload,
            format="json",
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_SERVICE_TOKEN,
        )

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
        self.assertEqual(response.data["active_alarm_count"], 0)

    def test_internal_ingest_requires_service_token_and_creates_alarms(self) -> None:
        payload = {
            "conveyor_id": "CV-01",
            "belt_speed_mps": 2.3,
            "alignment_offset_mm": 30.0,
            "volume_m3h": 500.0,
            "tear_probability": 0.5,
            "confidence": 0.95,
        }

        denied = self.internal_client.post("/api/telemetry/ingest/", payload, format="json")
        self.assertEqual(denied.status_code, 403)

        accepted = self.internal_client.post(
            "/api/telemetry/ingest/",
            payload,
            format="json",
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_SERVICE_TOKEN,
        )
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(TelemetrySample.objects.count(), 1)
        self.assertTrue(Alarm.objects.filter(code="ALIGNMENT_WARNING", active=True).exists())
        self.assertTrue(Alarm.objects.filter(code="TEAR_WARNING", active=True).exists())
        self.assertTrue(Alarm.objects.filter(code="OVERLOAD_CRITICAL", active=True).exists())

    def test_alarm_can_be_acknowledged_without_resolving_condition(self) -> None:
        alarm = Alarm.objects.create(
            conveyor=self.conveyor,
            condition_key="ALIGNMENT",
            code="ALIGNMENT_WARNING",
            severity=Alarm.Severity.WARNING,
            message="Alignment warning",
            active=True,
        )

        response = self.client.post(f"/api/events/{alarm.id}/acknowledge/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        alarm.refresh_from_db()
        self.assertTrue(alarm.acknowledged)
        self.assertTrue(alarm.active)
        self.assertIsNone(alarm.resolved_at)

    def test_latched_warning_is_not_recreated_after_ack(self) -> None:
        self.assertEqual(self._ingest(alignment_offset_mm=30.0).status_code, 201)
        alarm = Alarm.objects.get(condition_key="ALIGNMENT", active=True)
        self.client.post(f"/api/events/{alarm.id}/acknowledge/", {}, format="json")

        self.assertEqual(self._ingest(alignment_offset_mm=31.0).status_code, 201)
        self.assertEqual(Alarm.objects.filter(condition_key="ALIGNMENT").count(), 1)

        alarm.refresh_from_db()
        self.assertTrue(alarm.active)
        self.assertTrue(alarm.acknowledged)

    def test_recovery_resolves_latched_alarm_and_allows_new_occurrence(self) -> None:
        self._ingest(alignment_offset_mm=30.0)
        first = Alarm.objects.get(condition_key="ALIGNMENT", active=True)

        self._ingest(alignment_offset_mm=10.0)
        first.refresh_from_db()
        self.assertFalse(first.active)
        self.assertIsNotNone(first.resolved_at)

        self._ingest(alignment_offset_mm=30.0)
        alarms = Alarm.objects.filter(condition_key="ALIGNMENT").order_by("id")
        self.assertEqual(alarms.count(), 2)
        self.assertFalse(alarms.first().active)
        self.assertTrue(alarms.last().active)

    def test_warning_escalates_once_to_latched_critical(self) -> None:
        self._ingest(alignment_offset_mm=30.0)
        warning = Alarm.objects.get(condition_key="ALIGNMENT", active=True)
        self.assertEqual(warning.code, "ALIGNMENT_WARNING")

        self._ingest(alignment_offset_mm=45.0)
        warning.refresh_from_db()
        critical = Alarm.objects.get(condition_key="ALIGNMENT", active=True)
        self.assertFalse(warning.active)
        self.assertEqual(critical.code, "ALIGNMENT_CRITICAL")

        self._ingest(alignment_offset_mm=42.0)
        self.assertEqual(Alarm.objects.filter(condition_key="ALIGNMENT").count(), 2)

    def test_critical_remains_latched_until_full_recovery(self) -> None:
        self._ingest(alignment_offset_mm=45.0)
        critical = Alarm.objects.get(condition_key="ALIGNMENT", active=True)

        self._ingest(alignment_offset_mm=23.0)
        critical.refresh_from_db()
        self.assertTrue(critical.active)

        self._ingest(alignment_offset_mm=19.0)
        critical.refresh_from_db()
        self.assertFalse(critical.active)
        self.assertIsNotNone(critical.resolved_at)

    def test_events_can_filter_acknowledged_and_active_state(self) -> None:
        Alarm.objects.create(
            conveyor=self.conveyor,
            condition_key="A",
            code="A1",
            severity=Alarm.Severity.INFO,
            message="one",
            acknowledged=False,
            active=True,
        )
        Alarm.objects.create(
            conveyor=self.conveyor,
            condition_key="B",
            code="A2",
            severity=Alarm.Severity.INFO,
            message="two",
            acknowledged=True,
            active=False,
        )

        response = self.client.get("/api/events/?conveyor=CV-01&acknowledged=false&active=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "A1")

    def test_evidence_endpoint_rejects_alarm_without_ready_evidence(self) -> None:
        alarm = Alarm.objects.create(
            conveyor=self.conveyor,
            code="A1",
            severity=Alarm.Severity.WARNING,
            message="pending",
            evidence_status=Alarm.EvidenceStatus.PENDING,
        )

        response = self.client.get(f"/api/events/{alarm.id}/evidence/")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["status"], Alarm.EvidenceStatus.PENDING)

    @patch("apps.monitoring.views._minio_client")
    def test_evidence_endpoint_returns_presigned_urls(self, client_factory) -> None:
        alarm = Alarm.objects.create(
            conveyor=self.conveyor,
            code="A2",
            severity=Alarm.Severity.CRITICAL,
            message="ready",
            evidence_status=Alarm.EvidenceStatus.READY,
            snapshot_object="CV-01/alarm/snapshot.jpg",
            clip_object="CV-01/alarm/pre_event.mp4",
        )
        minio_client = MagicMock()
        minio_client.presigned_get_object.side_effect = [
            "http://localhost:9000/snapshot-signed",
            "http://localhost:9000/clip-signed",
        ]
        client_factory.return_value = minio_client

        response = self.client.get(f"/api/events/{alarm.id}/evidence/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["snapshot_url"], "http://localhost:9000/snapshot-signed")
        self.assertEqual(response.data["clip_url"], "http://localhost:9000/clip-signed")
