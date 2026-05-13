from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AuditEntry:
    actor: str
    action: str
    target: str


class AuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, actor: str, action: str, target: str) -> None:
        self._entries.append(AuditEntry(actor=actor, action=action, target=target))

    def entries(self) -> Iterable[AuditEntry]:
        return list(self._entries)

    def size(self) -> int:
        return len(self._entries)
