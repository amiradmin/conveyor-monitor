"""Run inside vision-service: python -m unittest test_video_localization."""
import unittest
import cv2
from app.video_monitor import VideoMonitor
from app.engine import analyze


class VideoLocalizationTests(unittest.TestCase):
    def test_both_edges_and_healthy_controls(self):
        monitor = VideoMonitor()
        capture = cv2.VideoCapture('/data/conveyor_1.mp4')
        self.assertTrue(capture.isOpened())
        try:
            for second, side in [(0, None), (6, None), (10, None), (12, None), (18, None), (20, None), (30, None), (4, 'left'), (14, 'left'), (15, 'left'), (16, 'left'), (17, 'left'), (24, 'left'), (36, 'right'), (37, 'right')]:
                with self.subTest(second=second):
                    capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
                    ok, frame = capture.read()
                    self.assertTrue(ok)
                    monitor._smoothed.clear()
                    result = analyze(monitor._estimate_metrics(frame, 30))
                    if side is None:
                        self.assertFalse(result.damage_regions)
                        self.assertEqual(result.tear_status, 'NORMAL')
                    else:
                        matching = [region for region in result.damage_regions if (region.x < .5) == (side == 'left')]
                        self.assertTrue(matching)
                        self.assertEqual(result.tear_status, 'CRITICAL')
                        self.assertTrue(result.stop_recommended)
                        for region in matching:
                            self.assertLessEqual(region.x + region.width, 1)
                            self.assertLessEqual(region.y + region.height, 1)
        finally:
            capture.release()
