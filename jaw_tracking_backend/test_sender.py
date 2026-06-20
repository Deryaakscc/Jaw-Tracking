from __future__ import annotations

import argparse
import json
import math
import socket
import time


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send simulated jaw_frame data to Unity over UDP.")
    parser.add_argument("--udp-ip", default="127.0.0.1")
    parser.add_argument("--udp-port", type=int, default=5055)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--duration-sec", type=float, default=0.0, help="0 means run until Ctrl+C.")
    parser.add_argument("--amplitude-mm", type=float, default=45.0)
    parser.add_argument("--amplitude-px", type=float, default=150.0)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    interval_sec = 1.0 / max(args.fps, 1.0)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_time = time.perf_counter()
    frame_id = 0

    print(f"Sending simulated jaw_frame UDP data to {args.udp_ip}:{args.udp_port}")
    print("Press Ctrl+C to stop.")

    try:
        while args.duration_sec <= 0 or time.perf_counter() - start_time < args.duration_sec:
            loop_started = time.perf_counter()
            elapsed = loop_started - start_time
            open_ratio = (math.sin(elapsed * 2.0) + 1.0) / 2.0

            frame = build_test_frame(
                frame_id=frame_id,
                fps=args.fps,
                open_ratio=open_ratio,
                amplitude_mm=args.amplitude_mm,
                amplitude_px=args.amplitude_px,
            )
            sock.sendto(json.dumps(frame).encode(), (args.udp_ip, args.udp_port))

            if frame_id % int(max(args.fps, 1.0)) == 0:
                print(
                    f"frame={frame_id} "
                    f"dy_mm={frame['relative']['dy_mm']:.1f} "
                    f"dy_px={frame['relative']['dy_px']:.1f}"
                )

            frame_id += 1
            sleep_time = interval_sec - (time.perf_counter() - loop_started)
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        sock.close()


def build_test_frame(
    frame_id: int,
    fps: float,
    open_ratio: float,
    amplitude_mm: float,
    amplitude_px: float,
) -> dict:
    ref_x_px = 340.0
    ref_y_px = 220.0
    dx_px = 12.0 * math.sin(frame_id * 0.08)
    dy_px = 45.0 + amplitude_px * open_ratio
    dz_px = 8.0 * math.sin(frame_id * 0.05)
    dtheta_deg = 10.0 * math.sin(frame_id * 0.06)

    dx_mm = 0.15 * dx_px
    dy_mm = amplitude_mm * open_ratio
    dz_mm = 0.15 * dz_px

    timestamp_ms = int(time.time() * 1000)
    latency_ms = 1000.0 / max(fps, 1.0)

    return {
        "type": "jaw_frame",
        "frame_id": frame_id,
        "timestamp_ms": timestamp_ms,
        "tracking_valid": True,
        "reference_marker": {
            "id": 0,
            "x_px": ref_x_px,
            "y_px": ref_y_px,
            "angle_deg": 0.0,
            "confidence": 1.0,
        },
        "jaw_marker": {
            "id": 1,
            "x_px": ref_x_px + dx_px,
            "y_px": ref_y_px + dy_px,
            "angle_deg": dtheta_deg,
            "confidence": 1.0,
        },
        "relative": {
            "dx_px": dx_px,
            "dy_px": dy_px,
            "dz_px": dz_px,
            "dtheta_deg": dtheta_deg,
            "dx_mm": dx_mm,
            "dy_mm": dy_mm,
            "dz_mm": dz_mm,
        },
        "pose": {
            "x_mm": dx_mm,
            "y_mm": dy_mm,
            "z_mm": 500.0 + dz_mm,
            "yaw_deg": dtheta_deg,
            "pitch_deg": 2.0 * math.sin(frame_id * 0.04),
            "roll_deg": 1.5 * math.sin(frame_id * 0.03),
        },
        "quality": {
            "latency_ms": latency_ms,
            "fps": fps,
            "confidence": 1.0,
        },
    }


if __name__ == "__main__":
    main()
