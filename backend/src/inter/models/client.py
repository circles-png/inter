from aiortc import RTCDataChannel, RTCPeerConnection


class Client:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection
        self.chat: RTCDataChannel | None = None
