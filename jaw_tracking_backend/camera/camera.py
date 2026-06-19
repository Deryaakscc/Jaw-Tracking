from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


class Camera:
    def __init__(
        self,
        index: int = 0,
        width: int = 640,
        height: int = 480,
        calibration_dir: str | Path = "jaw_tracking_backend/calibration",
        fallback_calibration_base: str | Path = "kamera_matrisi",
    ) -> None:
        self.index = index
        self.width = width
        self.height = height
        self.camera_matrix, self.dist_coeffs = load_camera_calibration(
            calibration_dir=calibration_dir,
            fallback_base=fallback_calibration_base,
        )

        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f"Camera could not be opened: index={index}")

    def read(self, undistort: bool = True) -> Tuple[bool, Optional[np.ndarray]]:
        ok, frame = self.cap.read()
        if not ok:
            return False, None

        if undistort and self.camera_matrix is not None and self.dist_coeffs is not None:
            frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)

        return True, frame

    def release(self) -> None:
        self.cap.release()


def load_camera_calibration(
    calibration_dir: str | Path = "jaw_tracking_backend/calibration",
    fallback_base: str | Path = "kamera_matrisi",
) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    calibration_path = Path(calibration_dir)
    matrix_path = calibration_path / "camera_matrix.npy"
    dist_path = calibration_path / "dist_coeffs.npy"

    if matrix_path.exists() and dist_path.exists():
        return np.load(matrix_path).astype(np.float32), np.load(dist_path).astype(np.float32)

    npz_path = Path(f"{fallback_base}.npz")
    if npz_path.exists():
        data = np.load(npz_path)
        matrix = data["camera_matrix"] if "camera_matrix" in data.files else data["mtx"] if "mtx" in data.files else None
        dist = data["dist_coeffs"] if "dist_coeffs" in data.files else data["dist"] if "dist" in data.files else None
        if matrix is not None and dist is not None:
            return matrix.astype(np.float32), dist.astype(np.float32)

    yaml_path = Path(f"{fallback_base}.yaml")
    if yaml_path.exists():
        matrix, dist = _load_simple_yaml_calibration(yaml_path)
        if matrix is not None and dist is not None:
            return matrix.astype(np.float32), dist.astype(np.float32)

    return None, None


def _load_simple_yaml_calibration(path: Path) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    try:
        import yaml

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return np.array(data["camera_matrix"], dtype=np.float32), np.array(data["dist_coeff"], dtype=np.float32)
    except Exception:
        fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
        if not fs.isOpened():
            return None, None
        matrix = fs.getNode("camera_matrix").mat()
        dist = fs.getNode("dist_coeff").mat()
        fs.release()
        return matrix, dist
