from aiortc import MediaStreamTrack, RTCDataChannel, RTCPeerConnection


class Client:
    def __init__(self, connection: RTCPeerConnection, viewer: str | None) -> None:
        self.connection = connection
        self.chat: RTCDataChannel | None = None
        self.tracks: list[MediaStreamTrack] = []
        self.viewer: str | None = viewer
