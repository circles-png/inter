from asyncio import Queue
from typing import Any
from aiortc import RTCPeerConnection
from aiortc.rtcrtpreceiver import RemoteStreamTrack
import aiortc.contrib.media

from inter.models.client import Client


class Stream:
    def __init__(self) -> None:
        self.connection: RTCPeerConnection | None = None
        self.tracks: tuple[RemoteStreamTrack, RemoteStreamTrack] | None = None
        self.clients: list[Client] = []
        self.relay = aiortc.contrib.media.MediaRelay()
        self.client_ws_queues: list[Queue[dict[str, Any]]] = []
        self.title: str = ""
        self.game: str = ""
        self.start: float | None = None
