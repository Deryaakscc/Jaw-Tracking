from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class MarkerFrame:
    id: int
    x_px: float
    y_px: float
    angle_deg: float
    confidence: float


@dataclass
class RelativeMovement:
    dx_px: float
    dy_px: float
    dz_px: float
    dtheta_deg: float
    dx_mm: Optional[float] = None
    dy_mm: Optional[float] = None
    dz_mm: Optional[float] = None


@dataclass
class JawPose:
    x_mm: float
    y_mm: float
    z_mm: float
    yaw_deg: float
    pitch_deg: float
    roll_deg: float


@dataclass
class Quality:
    latency_ms: float
    fps: float
    confidence: float


@dataclass
class JawFrame:
    type: str
    frame_id: int
    timestamp_ms: int
    tracking_valid: bool
    reference_marker: Optional[MarkerFrame]
    jaw_marker: Optional[MarkerFrame]
    relative: Optional[RelativeMovement]
    pose: Optional[JawPose]
    quality: Quality

    def to_dict(self) -> dict:
        return asdict(self)
