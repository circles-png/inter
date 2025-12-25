from asyncio import Queue
from aiortc import MediaStreamTrack, RTCPeerConnection
import aiortc.contrib.media

from inter.models.client import Client


class Stream:
    def __init__(self) -> None:
        self.connection: RTCPeerConnection | None = None
        self.tracks: list[MediaStreamTrack] = []
        self.clients: list[Client] = []
        self.relay = aiortc.contrib.media.MediaRelay()
        self.client_ws_queues: list[Queue[dict[str, str]]] = []
