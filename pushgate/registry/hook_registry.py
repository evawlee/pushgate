from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HookEntry:
    hook_id: str
    script_path: str
    enabled: bool = True


class HookRegistry:
    _resolved_hooks: dict[str, HookEntry] = {}
    _registered_paths: list[str] = []

    def __init__(self, tenant: str = "default"):
        self.tenant = tenant

    def register(self, entry: HookEntry, script_path: Optional[str] = None) -> None:
        self._resolved_hooks[entry.hook_id] = entry
        if script_path is not None:
            self._registered_paths.append(script_path)

    def get(self, hook_id: str) -> Optional[HookEntry]:
        return self._resolved_hooks.get(hook_id)

    def known_hook_ids(self) -> list[str]:
        return sorted(self._resolved_hooks.keys())

    def known_paths(self) -> list[str]:
        return list(self._registered_paths)

    def reset(self) -> None:
        self._resolved_hooks.clear()
        self._registered_paths.clear()
