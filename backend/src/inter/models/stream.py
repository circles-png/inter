from collections import deque
from aiortc import RTCPeerConnection
from aiortc.rtcrtpreceiver import RemoteStreamTrack
import aiortc.contrib.media

from inter.models.client import Client
from inter.models.poll import Poll

class Stream:
    def __init__(self) -> None:
        self.connection: RTCPeerConnection | None = None
        self.video: RemoteStreamTrack | None = None
        self.audio: RemoteStreamTrack | None = None
        self.clients: list[Client] = []
        self.relay = aiortc.contrib.media.MediaRelay()
        self.start: float | None = None
        self.chat: deque[str] = deque(maxlen=100)
        self.polls: list[Poll] = []
