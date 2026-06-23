from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from jaw_tracking_backend.detection.aruco_detector import DetectedMarker
from jaw_tracking_backend.models.jaw_frame import RelativeMovement


class JawMotionCalculator:
    def __init__(self, marker_size_mm: float = 30.0) -> None:
        self.marker_size_mm = marker_size_mm
        self.kalman_dx = self._create_kalman()
        self.kalman_dy = self._create_kalman()

    def calculate(
        self,
        reference: Optional[DetectedMarker],
        jaw: Optional[DetectedMarker],
    ) -> Optional[RelativeMovement]:
        if reference is None or jaw is None:
            return None

        dx_px = jaw.marker.x_px - reference.marker.x_px
        dy_px = jaw.marker.y_px - reference.marker.y_px
        dtheta_deg = _normalize_angle(jaw.marker.angle_deg - reference.marker.angle_deg)

        # Kalman filtresi ile düzeltme
        dx_px = self._apply_kalman(self.kalman_dx, dx_px)
        dy_px = self._apply_kalman(self.kalman_dy, dy_px)

        dz_px = 0.0
        dx_mm = dy_mm = dz_mm = None

        if reference.tvec is not None and jaw.tvec is not None:
            relative_tvec = jaw.tvec - reference.tvec
            dx_mm = float(relative_tvec[0])
            dy_mm = float(relative_tvec[1])
            dz_mm = float(relative_tvec[2])
            dz_px = _mm_to_reference_px(dz_mm, reference.corners, self.marker_size_mm)
        else:
            mm_per_px = _estimate_mm_per_px(reference.corners, self.marker_size_mm)
            if mm_per_px is not None:
                dx_mm = float(dx_px * mm_per_px)
                dy_mm = float(dy_px * mm_per_px)
                dz_mm = 0.0

        return RelativeMovement(
            dx_px=float(dx_px),
            dy_px=float(dy_px),
            dz_px=float(dz_px),
            dtheta_deg=float(dtheta_deg),
            dx_mm=dx_mm,
            dy_mm=dy_mm,
            dz_mm=dz_mm,
        )

    @staticmethod
    def _create_kalman() -> cv2.KalmanFilter:
        """Kalman filtresi oluştur (1D pozisyon ve hız için)."""
        kalman = cv2.KalmanFilter(2, 1)
        kalman.measurementMatrix = np.array([[1, 0]], np.float32)
        kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        kalman.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.005
        kalman.measurementNoiseCov = np.array([[1]], np.float32) * 0.2
        return kalman

    @staticmethod
    def _apply_kalman(kalman: cv2.KalmanFilter, measurement: float) -> float:
        """Ölçümü Kalman filtresinden geçir ve tahmin edilen değeri döndür."""
        kalman.correct(np.array([[np.float32(measurement)]]))
        prediction = kalman.predict()
        return float(prediction[0][0])


def _estimate_mm_per_px(corners: np.ndarray, marker_size_mm: float) -> Optional[float]:
    marker_width_px = float(np.linalg.norm(corners[1] - corners[0]))
    if marker_width_px <= 0:
        return None
    return marker_size_mm / marker_width_px


def _mm_to_reference_px(value_mm: float, corners: np.ndarray, marker_size_mm: float) -> float:
    mm_per_px = _estimate_mm_per_px(corners, marker_size_mm)
    if mm_per_px is None or mm_per_px <= 0:
        return 0.0
    return float(value_mm / mm_per_px)


def _normalize_angle(angle_deg: float) -> float:
    return (angle_deg + 180.0) % 360.0 - 180.0
