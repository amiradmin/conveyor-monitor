import os
import threading
import requests
from .video_monitor import VideoMonitor


class MonitorFleet:
    """One independent processing thread and evidence buffer per registered belt."""
    def __init__(self):
        self.workers = {}
        self.configs = {}
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None
        ingest = os.getenv("BACKEND_INGEST_URL", "http://backend:8000/api/telemetry/ingest/")
        self.catalog_url = ingest.split("/telemetry/ingest/")[0] + "/vision/sources/"

    def reconcile(self, sources):
        desired = {item["conveyor_id"]: item for item in sources}
        with self.lock:
            for code in list(self.workers):
                if code not in desired or desired[code] != self.configs[code]:
                    self.workers.pop(code).stop()
                    self.configs.pop(code)
            for code, item in desired.items():
                if code not in self.workers:
                    worker = VideoMonitor(source=item["source"], conveyor_id=code, belt_width_mm=item["belt_width_mm"], source_revision=item.get("revision", "legacy"))
                    self.workers[code] = worker
                    self.configs[code] = item
                    worker.start()

    def get(self, code):
        with self.lock:
            return self.workers.get(code)

    def diagnostics(self):
        with self.lock:
            return {code: worker.diagnostics() for code, worker in self.workers.items()}

    def _run(self):
        while not self.stop_event.is_set():
            try:
                response = requests.get(self.catalog_url, headers={"X-Internal-Token": os.getenv("INTERNAL_SERVICE_TOKEN", "dev-internal-token")}, timeout=3)
                response.raise_for_status()
                self.reconcile(response.json())
            except (requests.RequestException, ValueError, KeyError, TypeError):
                pass  # A temporary catalog outage keeps already registered workers running.
            self.stop_event.wait(5)

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="vision-fleet", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=4)
        self.reconcile([])
