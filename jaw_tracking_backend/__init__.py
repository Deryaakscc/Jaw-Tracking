"""Real-time jaw tracking backend package.

This package provides real-time jaw motion tracking using ArUco markers,
camera calibration, pose estimation, and UDP streaming to Unity.

Modules:
    camera: Camera handling and calibration
    detection: ArUco marker detection
    pose: 3D pose estimation from markers
    motion: Jaw motion calculation
    network: UDP data transmission
    models: Data models (JawFrame)
    utils: Utility functions (FPS counter)
"""

__version__ = "1.0.0"
__author__ = "Jaw Tracking Project"
