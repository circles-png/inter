from datetime import datetime
from uuid import uuid4


class Option:
    def __init__(self, text: str) -> None:
        self.text: str = text
        self.users: set[int] = set()


class Poll:
    def __init__(
        self, question: str, options: list[Option], duration: float, start: float
    ) -> None:
        self.id = uuid4().hex
        self.question = question
        self.options = options
        self.duration = duration
        self.start = start

    @property
    def finished(self) -> bool:
        return self.start + self.duration < datetime.now().timestamp()
