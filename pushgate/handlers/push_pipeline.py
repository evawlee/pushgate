from dataclasses import dataclass
from typing import Mapping, Optional

from pushgate.handlers.hook_script_loader import HookScriptLoader
from pushgate.handlers.hooks_dir_loader import HooksDirLoader
from pushgate.parsers.stat_header import StatHeaderEncoder, StatHeaderDecoder
from pushgate.registry.audit_log import AuditLog
from pushgate.registry.hook_registry import HookEntry, HookRegistry


@dataclass(frozen=True)
class PushOutcome:
    accepted: bool
    decoded_fields: dict[str, str]
    hook_id: Optional[str]


class PushPipeline:
    def __init__(
        self,
        registry: HookRegistry,
        dir_loader: HooksDirLoader,
        script_loader: HookScriptLoader,
        encoder: Optional[StatHeaderEncoder] = None,
        decoder: Optional[StatHeaderDecoder] = None,
        audit: Optional[AuditLog] = None,
    ):
        self.registry = registry
        self.dir_loader = dir_loader
        self.script_loader = script_loader
        self.encoder = encoder or StatHeaderEncoder()
        self.decoder = decoder or StatHeaderDecoder()
        self.audit = audit or AuditLog()

    def encode_push_options(self, options: Mapping[str, str]) -> str:
        return self.encoder.encode(options)

    def relay(self, raw_header: str, hook_id: str) -> PushOutcome:
        fields = self.decoder.decode(raw_header)
        entry = self.registry.get(hook_id)
        accepted = entry is not None and entry.enabled
        if accepted:
            self.audit.append(
                actor=fields.get("user", "unknown"),
                action="push",
                target=hook_id,
            )
        return PushOutcome(accepted=accepted, decoded_fields=fields, hook_id=hook_id)

    def register_hook(self, hook_id: str, script_name: str) -> HookEntry:
        path = self.script_loader.resolve(script_name)
        entry = HookEntry(hook_id=hook_id, script_path=path, enabled=True)
        self.registry.register(entry, script_path=path)
        return entry
