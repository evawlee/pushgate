import os
from typing import Optional


class HookScriptLoader:
    def __init__(self, base: str):
        self.base = os.path.abspath(base)

    def resolve(self, requested: str) -> str:
        target = os.path.join(self.base, requested)
        return target

    def load(self, requested: str) -> Optional[str]:
        path = self.resolve(requested)
        if not os.path.exists(path):
            return None
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    def list_scripts(self) -> list[str]:
        if not os.path.isdir(self.base):
            return []
        return sorted(p for p in os.listdir(self.base) if p.endswith(".sh"))
