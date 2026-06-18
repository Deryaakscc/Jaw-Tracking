from __future__ import annotations

import argparse
import time

import cv2

from jaw_tracking_backend.camera.camera import Camera
from jaw_tracking_backend.detection.aruco_detector import ArucoDetector
from jaw_tracking_backend.models.jaw_frame import JawFrame, Quality
from jaw_tracking_backend.motion.jaw_motion import JawMotionCalculator
from jaw_tracking_backend.network.udp_sender import UDPSender
from jaw_tracking_backend.pose.pose_estimator import PoseEstimator
from jaw_tracking_backend.utils.fps_counter import FPSCounter


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Real-time jaw tracking over UDP for Unity.")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--reference-id", type=int, default=0)
    parser.add_argument("--jaw-id", type=int, default=1)
    parser.add_argument("--marker-size-mm", type=float, default=30.0)
    parser.add_argument("--calibration-dir", default="jaw_tracking_backend/calibration")
    parser.add_argument("--fallback-calibration-base", default="kamera_matrisi")
    parser.add_argument("--udp-ip", default="127.0.0.1")
    parser.add_argument("--udp-port", type=int, default=5055)
    parser.add_argument("--headless", action="store_true", help="Do not open an OpenCV preview window.")
    parser.add_argument("--no-undistort", action="store_true", help="Skip frame undistortion.")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    camera = Camera(
        index=args.camera_index,
        width=args.width,
        height=args.height,
        calibration_dir=args.calibration_dir,
        fallback_calibration_base=args.fallback_calibration_base,
    )
    detector = ArucoDetector(marker_size_mm=args.marker_size_mm)
    motion = JawMotionCalculator(marker_size_mm=args.marker_size_mm)
    pose_estimator = PoseEstimator()
    udp_sender = UDPSender(ip=args.udp_ip, port=args.udp_port)
    fps_counter = FPSCounter()

    frame_id = 0

    try:
        while True:
            frame_start = time.perf_counter()
            timestamp_ms = int(time.time() * 1000)
            ok, frame = camera.read(undistort=not args.no_undistort)
            if not ok or frame is None:
                break

            detections = detector.detect(frame, camera.camera_matrix, camera.dist_coeffs)
            reference = detections.get(args.reference_id)
            jaw = detections.get(args.jaw_id)
            tracking_valid = reference is not None and jaw is not None

            relative = motion.calculate(reference, jaw) if tracking_valid else None
            pose = pose_estimator.estimate(jaw) if tracking_valid else None
            confidence = _quality_confidence(reference, jaw) if tracking_valid else 0.0
            fps = fps_counter.tick()
            latency_ms = (time.perf_counter() - frame_start) * 1000.0

            jaw_frame = JawFrame(
                type="jaw_frame",
                frame_id=frame_id,
                timestamp_ms=timestamp_ms,
                tracking_valid=tracking_valid,
                reference_marker=reference.marker if reference is not None else None,
                jaw_marker=jaw.marker if jaw is not None else None,
                relative=relative,
                pose=pose,
                quality=Quality(latency_ms=latency_ms, fps=fps, confidence=confidence),
            )

            udp_sender.send(jaw_frame.to_dict())

            if not args.headless:
                _draw_overlay(frame, detector, detections, jaw_frame)
                cv2.imshow("Jaw Tracking UDP", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            frame_id += 1
    finally:
        camera.release()
        udp_sender.close()
        if not args.headless:
            cv2.destroyAllWindows()


def _quality_confidence(reference, jaw) -> float:
    return min(reference.marker.confidence, jaw.marker.confidence)


def _draw_overlay(frame, detector: ArucoDetector, detections: dict, jaw_frame: JawFrame) -> None:
    detector.draw(frame, detections)

    color = (0, 220, 0) if jaw_frame.tracking_valid else (0, 0, 255)
    status = "tracking" if jaw_frame.tracking_valid else "marker missing"
    cv2.putText(frame, status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(
        frame,
        f"fps: {jaw_frame.quality.fps:.1f} latency: {jaw_frame.quality.latency_ms:.1f} ms",
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
    )

    if jaw_frame.relative is not None:
        rel = jaw_frame.relative
        cv2.putText(
            frame,
            f"dx {rel.dx_px:.1f}px dy {rel.dy_px:.1f}px dz {rel.dz_px:.1f}px dtheta {rel.dtheta_deg:.1f}deg",
            (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
        )


if __name__ == "__main__":
    main()
