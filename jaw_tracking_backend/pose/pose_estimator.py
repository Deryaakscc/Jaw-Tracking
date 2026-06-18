from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from jaw_tracking_backend.detection.aruco_detector import DetectedMarker
from jaw_tracking_backend.models.jaw_frame import JawPose


class PoseEstimator:
    def estimate(self, marker: Optional[DetectedMarker]) -> Optional[JawPose]:
        if marker is None or marker.rvec is None or marker.tvec is None:
            return None

        rotation_matrix, _ = cv2.Rodrigues(marker.rvec)
        yaw, pitch, roll = _rotation_matrix_to_euler_deg(rotation_matrix)

        return JawPose(
            x_mm=float(marker.tvec[0]),
            y_mm=float(marker.tvec[1]),
            z_mm=float(marker.tvec[2]),
            yaw_deg=float(yaw),
            pitch_deg=float(pitch),
            roll_deg=float(roll),
        )


def _rotation_matrix_to_euler_deg(rotation_matrix: np.ndarray) -> tuple[float, float, float]:
    sy = float(np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2))
    singular = sy < 1e-6

    if not singular:
        roll = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
        pitch = np.arctan2(-rotation_matrix[2, 0], sy)
        yaw = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
    else:
        roll = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
        pitch = np.arctan2(-rotation_matrix[2, 0], sy)
        yaw = 0.0

    return tuple(float(value) for value in np.degrees([yaw, pitch, roll]))
