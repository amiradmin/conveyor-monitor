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

    def test_damage_location_matches_alarm_and_clears_on_healthy_frame(self) -> None:
        regions = [{"x": 0.17, "y": 0.25, "width": 0.10, "height": 0.33, "score": 0.87}]
        response = self._ingest(tear_probability=0.40, damage_regions=regions, source_position_seconds=4.0)
        self.assertEqual(response.status_code, 201)
        status = self.client.get("/api/conveyors/CV-01/status/").data
        self.assertEqual(status["damage_regions"], regions)
        self.assertEqual(status["source_position_seconds"], 4.0)
        self.assertEqual(status["tear_status"], "CRITICAL")
        self.assertEqual(status["tear_probability"], 0.40)
        self.assertTrue(Alarm.objects.filter(code="TEAR_CRITICAL", active=True).exists())
        self._ingest(damage_regions=[], source_position_seconds=6.0)
        status = self.client.get("/api/conveyors/CV-01/status/").data
        self.assertEqual(status["damage_regions"], [])
        self.assertFalse(Alarm.objects.filter(code="TEAR_CRITICAL", active=True).exists())

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

    def test_cv02_telemetry_and_alarms_are_isolated(self):
        self._ingest(conveyor_id="CV-02", tear_probability=.8, anomaly_score=.8,
                     anomaly_regions=[[.7, .2, .04, .2]])
        response = self.client.get("/api/conveyors/CV-02/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["conveyor"], "CV-02")
        self.assertEqual(response.data["vision_details"]["anomaly_score"], .8)
        self.assertTrue(Alarm.objects.filter(conveyor__code="CV-02", code="BELT_ANOMALY_CRITICAL").exists())
        self.assertEqual(self.conveyor.samples.count(), 0)
        self.assertEqual(self.client.get("/api/events/?conveyor=CV-01").data, [])

    @patch("apps.monitoring.views.requests.get")
    def test_refresh_rejects_telemetry_from_another_camera(self, get):
        from .views import _refresh_from_vision
        get.return_value.json.return_value = {"conveyor_id": "CV-01", "tear_probability": .9}
        cv02 = Conveyor.objects.create(code="CV-02", name="Second belt")
        self.assertIsNone(_refresh_from_vision(cv02))
        self.assertEqual(cv02.samples.count(), 0)
        self.assertEqual(get.call_args.kwargs["params"], {"conveyor_id": "CV-02"})

    @patch("apps.monitoring.views.requests.get")
    def test_cv02_preview_requires_authentication_and_routes_camera(self, get):
        get.return_value.content = b"jpeg"
        self.assertEqual(self.internal_client.get("/api/conveyors/CV-02/frame/").status_code, 401)
        response = self.client.get("/api/conveyors/CV-02/frame/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"jpeg")
        self.assertEqual(get.call_args.kwargs["params"], {"conveyor_id": "CV-02"})

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


@override_settings(EVIDENCE_CAPTURE_ENABLED=False)
class FleetApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username="fleet-operator"))
        self.first = Conveyor.objects.create(code="CV-01", name="First belt")
        self.second = Conveyor.objects.create(code="CV-02", name="Second belt")

    def test_fleet_status_and_events_are_independent(self):
        TelemetrySample.objects.create(conveyor=self.first, speed_mps=1, volume_m3h=10)
        TelemetrySample.objects.create(conveyor=self.second, speed_mps=3, volume_m3h=30)
        Alarm.objects.create(conveyor=self.second, condition_key="tear", code="TEAR_CRITICAL", severity="CRITICAL", message="Second only", active=True)
        fleet = {item["code"]: item for item in self.client.get("/api/conveyors/").data}
        self.assertEqual(fleet["CV-01"]["status"]["speed_mps"], 1)
        self.assertEqual(fleet["CV-02"]["status"]["speed_mps"], 3)
        self.assertEqual(fleet["CV-01"]["pending_alarm_count"], 0)
        self.assertEqual(fleet["CV-02"]["pending_alarm_count"], 1)
        self.assertEqual(self.client.get("/api/events/?conveyor=CV-01").data, [])
        self.assertEqual(len(self.client.get("/api/events/?conveyor=CV-02").data), 1)

    def test_unknown_status_does_not_register_a_belt(self):
        self.assertEqual(self.client.get("/api/conveyors/UNKNOWN/status/").status_code, 404)
        self.assertFalse(Conveyor.objects.filter(code="UNKNOWN").exists())

    @patch("apps.monitoring.views.requests.get")
    def test_refresh_rejects_another_conveyors_video(self, get):
        get.return_value.json.return_value = {"conveyor_id": "CV-01", "belt_speed_mps": 9}
        response = self.client.get("/api/conveyors/CV-02/status/")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(self.second.samples.exists())
        self.assertTrue(get.call_args.args[0].endswith("/conveyors/CV-02/live"))

    def test_register_edit_and_disable_video_source(self):
        response = self.client.post("/api/conveyors/", {"code": "CV-03", "name": "Third", "camera_name": "Top camera", "video_source": "conveyor_1_old.mp4"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["video_source"], "conveyor_1_old.mp4")
        self.assertEqual(self.client.post("/api/conveyors/", {"code": "CV-03", "name": "Duplicate", "video_source": "conveyor_1.mp4"}, format="json").status_code, 400)
        internal = APIClient()
        self.assertEqual(internal.get("/api/vision/sources/").status_code, 403)
        headers = {"HTTP_X_INTERNAL_TOKEN": settings.INTERNAL_SERVICE_TOKEN}
        sources = internal.get("/api/vision/sources/", **headers).data
        source = next(item for item in sources if item["conveyor_id"] == "CV-03")
        self.assertEqual(source["source"], "/data/conveyor_1_old.mp4")
        old = internal.post("/api/telemetry/ingest/", {"conveyor_id": "CV-03", "source_revision": "obsolete"}, format="json", **headers)
        self.assertEqual(old.status_code, 409)
        current = internal.post("/api/telemetry/ingest/", {"conveyor_id": "CV-03", "source_revision": source["revision"], "belt_speed_mps": 2}, format="json", **headers)
        self.assertEqual(current.status_code, 201)
        self.client.patch("/api/conveyors/CV-03/", {"active": False}, format="json")
        self.assertEqual(self.client.get("/api/conveyors/CV-03/status/").data["state"], "DISABLED")
        self.assertNotIn("CV-03", [item["conveyor_id"] for item in internal.get("/api/vision/sources/", **headers).data])
        self.assertEqual(internal.post("/api/telemetry/ingest/", {"conveyor_id": "CV-03", "source_revision": source["revision"]}, format="json", **headers).status_code, 409)

    @patch("apps.monitoring.views.requests.get")
    def test_replacing_source_invalidates_previous_telemetry(self, get):
        TelemetrySample.objects.create(conveyor=self.second, speed_mps=8)
        self.client.patch("/api/conveyors/CV-02/", {"video_source": "conveyor_1.mp4"}, format="json")
        get.side_effect = __import__("requests").ConnectionError()
        self.assertEqual(self.client.get("/api/conveyors/CV-02/status/").status_code, 503)
        fleet = self.client.get("/api/conveyors/").data
        self.assertIsNone(next(item for item in fleet if item["code"] == "CV-02")["status"])
        self.assertEqual(self.second.samples.count(), 1)

    def test_upload_and_playback_require_login(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Camera
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            video = SimpleUploadedFile("test.mp4", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 30, content_type="video/mp4")
            response = self.client.post("/api/conveyors/", {"code": "CV-04", "name": "Uploaded", "video_file": video}, format="multipart")
            self.assertEqual(response.status_code, 201)
            self.assertTrue(Camera.objects.get(conveyor__code="CV-04").video_file.name.startswith("videos/"))
            playback = self.client.get("/api/conveyors/CV-04/video/")
            self.assertEqual(playback.status_code, 200)
            self.assertTrue(b"ftyp" in b"".join(playback.streaming_content))
            self.assertEqual(APIClient().get("/api/conveyors/CV-04/video/").status_code, 401)
            invalid = SimpleUploadedFile("fake.mp4", b"not a video")
            self.assertEqual(self.client.post("/api/conveyors/", {"code": "CV-05", "name": "Invalid", "video_file": invalid}, format="multipart").status_code, 400)
            self.assertEqual(self.client.post("/api/conveyors/", {"code": "CV-05", "name": "Bad path", "video_source": "../secret.mp4"}, format="json").status_code, 400)
