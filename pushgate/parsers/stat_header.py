from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StatField:
    key: str
    value: str


class StatHeaderEncoder:
    def __init__(self, peer_id: str = "babeld-analog"):
        self.peer_id = peer_id

    def encode(self, fields: Mapping[str, str]) -> str:
        parts = [f"peer={self.peer_id}"]
        for key, value in fields.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("StatHeaderEncoder only accepts str key/value")
            parts.append(f"{key}={value}")
        return ";".join(parts)


class StatHeaderDecoder:
    def __init__(self) -> None:
        self._cached_peer: str = ""

    def decode(self, raw: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for chunk in raw.split(";"):
            if not chunk:
                continue
            if "=" not in chunk:
                continue
            k, _, v = chunk.partition("=")
            out[k.strip()] = v
        self._cached_peer = out.get("peer", "")
        return out

    @property
    def cached_peer(self) -> str:
        return self._cached_peer
