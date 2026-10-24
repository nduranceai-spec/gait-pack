import unittest
from unittest.mock import patch

import cv2

from src.cameras import (
    CameraDevice,
    _find_indexed_cameras,
    find_cameras,
    open_camera,
    select_camera,
)


class CameraDiscoveryTests(unittest.TestCase):
    def test_windows_uses_directshow_and_falls_back_to_media_foundation(self):
        with (
            patch("src.cameras.sys.platform", "win32"),
            patch("src.cameras._find_indexed_cameras", side_effect=[[], [CameraDevice(0, "Camera 0", "unknown")]]) as discover,
        ):
            cameras = find_cameras()

        self.assertEqual([cv2.CAP_DSHOW, cv2.CAP_MSMF], [call.args[0] for call in discover.call_args_list])
        self.assertEqual([0], [camera.path for camera in cameras])

    def test_indexed_discovery_reports_readable_devices_and_releases_capture(self):
        captures = []

        class Capture:
            def __init__(self, index, backend):
                self.index = index
                self.backend = backend
                self.released = False
                captures.append(self)

            def isOpened(self):
                return True

            def read(self):
                return self.index == 1, object() if self.index == 1 else None

            def release(self):
                self.released = True

        with (
            patch("src.cameras.MAX_CAMERA_INDEX", 2),
            patch("src.cameras.cv2.VideoCapture", Capture),
        ):
            cameras = _find_indexed_cameras(cv2.CAP_DSHOW)

        self.assertEqual([1], [camera.path for camera in cameras])
        self.assertTrue(all(capture.released for capture in captures))
        self.assertEqual([cv2.CAP_DSHOW, cv2.CAP_DSHOW], [capture.backend for capture in captures])

    def test_numeric_selection_matches_cross_platform_camera_index(self):
        camera = CameraDevice(2, "Camera 2", "unknown")

        self.assertIs(camera, select_camera("2", [camera]))

    def test_numeric_selection_matches_linux_video_node(self):
        camera = CameraDevice("/dev/video2", "USB camera", "usb")

        self.assertIs(camera, select_camera("2", [camera]))

    def test_single_unidentified_camera_is_selected_for_default_usb_choice(self):
        camera = CameraDevice(0, "Camera 0", "unknown")

        self.assertIs(camera, select_camera("usb", [camera]))

    def test_open_camera_passes_numeric_index_and_native_backend(self):
        camera = CameraDevice(3, "Camera 3", "unknown", backend=cv2.CAP_DSHOW)

        class Capture:
            def set(self, _property, _value):
                return True

        capture = Capture()

        with patch("src.cameras.cv2.VideoCapture", return_value=capture) as open_capture:
            result = open_camera(camera)

        self.assertIs(capture, result)
        self.assertEqual((3, cv2.CAP_DSHOW), open_capture.call_args.args)


if __name__ == "__main__":
    unittest.main()
