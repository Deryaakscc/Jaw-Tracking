from __future__ import annotations

import json
import socket
from typing import Any


class UDPSender:
    def __init__(self, ip: str = "127.0.0.1", port: int = 5055) -> None:
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, frame: dict[str, Any]) -> None:
        self.sock.sendto(json.dumps(frame).encode(), (self.ip, self.port))

    def close(self) -> None:
        self.sock.close()
