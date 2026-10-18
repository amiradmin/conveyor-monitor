import unittest
from unittest.mock import patch, MagicMock
from app.fleet import MonitorFleet
from app.video_monitor import VideoMonitor

class FleetTests(unittest.TestCase):
    @patch('app.fleet.VideoMonitor')
    def test_reconcile_keeps_independent_workers_and_replaces_only_changed_source(self, factory):
        fleet = MonitorFleet()
        first = {'conveyor_id': 'CV-01', 'source': '/data/a.mp4', 'belt_width_mm': 1200, 'revision': 'a'}
        second = {'conveyor_id': 'CV-02', 'source': '/data/b.mp4', 'belt_width_mm': 1500, 'revision': 'b'}
        factory.side_effect = [MagicMock() for _ in range(3)]
        fleet.reconcile([first, second])
        old_first, old_second = fleet.get('CV-01'), fleet.get('CV-02')
        fleet.reconcile([first, {**second, 'revision': 'new'}])
        self.assertIs(fleet.get('CV-01'), old_first)
        self.assertIsNot(fleet.get('CV-02'), old_second)
        old_first.stop.assert_not_called()
        old_second.stop.assert_called_once()
        fleet.reconcile([first])
        self.assertIsNone(fleet.get('CV-02'))
        self.assertEqual(factory.call_args.kwargs['conveyor_id'], 'CV-02')

    def test_evidence_cannot_use_another_belts_buffer(self):
        monitor = VideoMonitor(source='/data/b.mp4', conveyor_id='CV-02')
        with self.assertRaisesRegex(ValueError, 'different conveyor'):
            monitor.capture_evidence({'alarm_id': 1, 'conveyor_id': 'CV-01'})

class FileProcessingTests(unittest.TestCase):
    def test_two_video_files_publish_their_own_identifiers_and_buffers(self):
        import time
        monitors = [VideoMonitor(source='/data/conveyor_1.mp4', conveyor_id='CV-01'),
                    VideoMonitor(source='/data/conveyor_1_old.mp4', conveyor_id='CV-02')]
        try:
            for monitor in monitors:
                monitor._push_backend = lambda result: None
                monitor.start()
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and not all(m.latest() for m in monitors):
                time.sleep(.1)
            self.assertEqual([m.latest().conveyor_id for m in monitors], ['CV-01', 'CV-02'])
            self.assertIsNot(monitors[0]._evidence_frames, monitors[1]._evidence_frames)
            self.assertTrue(all(m.diagnostics()['evidence_buffer_frames'] > 0 for m in monitors))
        finally:
            for monitor in monitors:
                monitor.stop()

if __name__ == '__main__':
    unittest.main()
