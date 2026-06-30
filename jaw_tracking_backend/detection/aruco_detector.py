from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from jaw_tracking_backend.models.jaw_frame import MarkerFrame


@dataclass
class DetectedMarker:
    marker: MarkerFrame
    corners: np.ndarray
    rvec: Optional[np.ndarray] = None
    tvec: Optional[np.ndarray] = None


class ArucoDetector:
    def __init__(
        self,
        dictionary_name: int = cv2.aruco.DICT_4X4_50,
        marker_size_mm: float = 30.0,
    ) -> None:
        self.marker_size_mm = marker_size_mm
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_name)
        self.parameters = cv2.aruco.DetectorParameters()
        self._detector = self._create_detector()

    def detect(
        self,
        frame: np.ndarray,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
    ) -> dict[int, DetectedMarker]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self._detector is not None:
            corners, ids, _ = self._detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)

        if ids is None:
            return {}

        poses = self._estimate_poses(corners, camera_matrix, dist_coeffs)
        detections: dict[int, DetectedMarker] = {}

        for index, marker_id_array in enumerate(ids):
            marker_id = int(marker_id_array[0])
            marker_corners = corners[index][0].astype(np.float32)
            center = marker_corners.mean(axis=0)
            angle = _marker_angle_deg(marker_corners)
            rvec, tvec = poses[index] if poses else (None, None)

            detections[marker_id] = DetectedMarker(
                marker=MarkerFrame(
                    id=marker_id,
                    x_px=float(center[0]),
                    y_px=float(center[1]),
                    angle_deg=float(angle),
                    confidence=1.0,
                ),
                corners=marker_corners,
                rvec=rvec,
                tvec=tvec,
            )

        return detections

    def draw(self, frame: np.ndarray, detections: dict[int, DetectedMarker]) -> None:
        if not detections:
            return
        corners = [detection.corners.reshape(1, 4, 2) for detection in detections.values()]
        ids = np.array([[marker_id] for marker_id in detections.keys()], dtype=np.int32)
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    def _create_detector(self):
        if hasattr(cv2.aruco, "ArucoDetector"):
            return cv2.aruco.ArucoDetector(self.aruco_dict, self.parameters)
        return None

    def _estimate_poses(
        self,
        corners: list[np.ndarray],
        camera_matrix: Optional[np.ndarray],
        dist_coeffs: Optional[np.ndarray],
    ) -> list[tuple[Optional[np.ndarray], Optional[np.ndarray]]]:
        if camera_matrix is None or dist_coeffs is None:
            return []

        
        half_size = self.marker_size_mm / 2.0
        obj_points = np.array([
            [-half_size,  half_size, 0], # Sol üst köşe
            [ half_size,  half_size, 0], # Sağ üst köşe
            [ half_size, -half_size, 0], # Sağ alt köşe
            [-half_size, -half_size, 0]  # Sol alt köşe
        ], dtype=np.float32)

        poses = []
        
        for corner in corners:
            
            image_points = corner.reshape((4, 2))

            success, rvec, tvec = cv2.solvePnP(
                objectPoints=obj_points, 
                imagePoints=image_points, 
                cameraMatrix=camera_matrix, 
                distCoeffs=dist_coeffs, 
                flags=cv2.SOLVEPNP_IPPE_SQUARE  # Özel parametremiz
            )
            
            if success:
                poses.append((rvec, tvec))
            else:
                poses.append((None, None))
                
        return poses

def _marker_angle_deg(corners: np.ndarray) -> float:
    edge = corners[1] - corners[0]
    return float(np.degrees(np.arctan2(edge[1], edge[0])))
