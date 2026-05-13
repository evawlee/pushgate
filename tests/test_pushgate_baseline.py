import os
import pytest

from pushgate.handlers.hook_script_loader import HookScriptLoader
from pushgate.handlers.hooks_dir_loader import HooksDirLoader
from pushgate.handlers.push_pipeline import PushPipeline
from pushgate.parsers.stat_header import StatHeaderDecoder, StatHeaderEncoder
from pushgate.registry.audit_log import AuditLog
from pushgate.registry.hook_registry import HookEntry, HookRegistry


class TestStatHeaderEncoderHappyPath:
    def test_encode_with_peer_only(self):
        enc = StatHeaderEncoder(peer_id="proxy1")
        result = enc.encode({})
        assert result == "peer=proxy1"

    def test_encode_with_one_field(self):
        enc = StatHeaderEncoder(peer_id="proxy1")
        result = enc.encode({"user": "alice"})
        assert "peer=proxy1" in result
        assert "user=alice" in result

    def test_encode_with_multiple_fields(self):
        enc = StatHeaderEncoder(peer_id="proxy1")
        result = enc.encode({"user": "alice", "repo": "main"})
        assert result.startswith("peer=proxy1;")
        assert "user=alice" in result
        assert "repo=main" in result

    def test_encode_rejects_non_str_value(self):
        enc = StatHeaderEncoder()
        with pytest.raises(TypeError):
            enc.encode({"user": 42})

    def test_encode_rejects_non_str_key(self):
        enc = StatHeaderEncoder()
        with pytest.raises(TypeError):
            enc.encode({1: "x"})

    def test_default_peer_id(self):
        enc = StatHeaderEncoder()
        assert enc.peer_id == "babeld-analog"


class TestStatHeaderDecoderHappyPath:
    def test_decode_peer_only(self):
        dec = StatHeaderDecoder()
        out = dec.decode("peer=proxy1")
        assert out == {"peer": "proxy1"}

    def test_decode_two_fields(self):
        dec = StatHeaderDecoder()
        out = dec.decode("peer=proxy1;user=alice")
        assert out["peer"] == "proxy1"
        assert out["user"] == "alice"

    def test_decode_empty_segments_skipped(self):
        dec = StatHeaderDecoder()
        out = dec.decode("peer=proxy1;;user=alice")
        assert out == {"peer": "proxy1", "user": "alice"}

    def test_decode_caches_peer(self):
        dec = StatHeaderDecoder()
        dec.decode("peer=proxy2;user=alice")
        assert dec.cached_peer == "proxy2"

    def test_decode_segment_without_eq_skipped(self):
        dec = StatHeaderDecoder()
        out = dec.decode("peer=proxy1;noeq;user=alice")
        assert out == {"peer": "proxy1", "user": "alice"}


class TestHooksDirLoaderHappyPath:
    def test_resolve_normal_filename(self, tmp_hooks_root):
        loader = HooksDirLoader(tmp_hooks_root)
        out = loader.resolve("pre-receive")
        assert out.endswith("pre-receive")
        assert out.startswith(tmp_hooks_root)

    def test_load_normal_filename(self, tmp_hooks_root):
        loader = HooksDirLoader(tmp_hooks_root)
        data = loader.load("pre-receive")
        assert data == b"ok pre"

    def test_load_missing_returns_none(self, tmp_hooks_root):
        loader = HooksDirLoader(tmp_hooks_root)
        assert loader.load("no-such-file") is None

    def test_list_dir(self, tmp_hooks_root):
        loader = HooksDirLoader(tmp_hooks_root)
        names = loader.list_dir()
        assert "pre-receive" in names
        assert "post-receive.sh" in names

    def test_base_is_absolute(self, tmp_hooks_root):
        loader = HooksDirLoader(tmp_hooks_root)
        assert os.path.isabs(loader.base)


class TestHookScriptLoaderHappyPath:
    def test_resolve_normal_filename(self, tmp_hooks_root):
        loader = HookScriptLoader(tmp_hooks_root)
        out = loader.resolve("post-receive.sh")
        assert out.endswith("post-receive.sh")
        assert out.startswith(tmp_hooks_root)

    def test_load_normal_filename(self, tmp_hooks_root):
        loader = HookScriptLoader(tmp_hooks_root)
        data = loader.load("post-receive.sh")
        assert data == "ok post"

    def test_load_missing_returns_none(self, tmp_hooks_root):
        loader = HookScriptLoader(tmp_hooks_root)
        assert loader.load("nope.sh") is None

    def test_list_scripts(self, tmp_hooks_root):
        loader = HookScriptLoader(tmp_hooks_root)
        names = loader.list_scripts()
        assert names == ["post-receive.sh"]

    def test_base_is_absolute(self, tmp_hooks_root):
        loader = HookScriptLoader(tmp_hooks_root)
        assert os.path.isabs(loader.base)


class TestHookRegistryHappyPath:
    def test_register_and_get(self):
        reg = HookRegistry(tenant="t1")
        entry = HookEntry(hook_id="h1", script_path="/a/b.sh")
        reg.register(entry)
        assert reg.get("h1") == entry

    def test_get_unknown_returns_none(self):
        reg = HookRegistry()
        assert reg.get("unknown") is None

    def test_known_hook_ids_sorted(self):
        reg = HookRegistry()
        reg.register(HookEntry(hook_id="b", script_path="/x"))
        reg.register(HookEntry(hook_id="a", script_path="/y"))
        assert reg.known_hook_ids() == ["a", "b"]

    def test_register_records_path(self):
        reg = HookRegistry()
        reg.register(HookEntry(hook_id="h1", script_path="/x.sh"), script_path="/x.sh")
        assert "/x.sh" in reg.known_paths()

    def test_default_tenant(self):
        reg = HookRegistry()
        assert reg.tenant == "default"

    def test_reset_clears(self):
        reg = HookRegistry()
        reg.register(HookEntry(hook_id="h1", script_path="/x"))
        reg.reset()
        assert reg.get("h1") is None
        assert reg.known_paths() == []


class TestAuditLogHappyPath:
    def test_append_increases_size(self):
        log = AuditLog()
        log.append(actor="alice", action="push", target="h1")
        assert log.size() == 1

    def test_entries_returns_appended(self):
        log = AuditLog()
        log.append(actor="alice", action="push", target="h1")
        entries = list(log.entries())
        assert len(entries) == 1
        assert entries[0].actor == "alice"

    def test_initial_size_zero(self):
        log = AuditLog()
        assert log.size() == 0


class TestPushPipelineHappyPath:
    def _build(self, tmp_hooks_root):
        reg = HookRegistry()
        dl = HooksDirLoader(tmp_hooks_root)
        sl = HookScriptLoader(tmp_hooks_root)
        return PushPipeline(registry=reg, dir_loader=dl, script_loader=sl)

    def test_encode_then_relay_known_hook(self, tmp_hooks_root):
        pipe = self._build(tmp_hooks_root)
        pipe.register_hook("h1", "post-receive.sh")
        raw = pipe.encode_push_options({"user": "alice"})
        outcome = pipe.relay(raw, hook_id="h1")
        assert outcome.accepted is True
        assert outcome.decoded_fields["user"] == "alice"

    def test_relay_unknown_hook_rejected(self, tmp_hooks_root):
        pipe = self._build(tmp_hooks_root)
        raw = pipe.encode_push_options({"user": "bob"})
        outcome = pipe.relay(raw, hook_id="missing")
        assert outcome.accepted is False

    def test_relay_writes_audit_when_accepted(self, tmp_hooks_root):
        pipe = self._build(tmp_hooks_root)
        pipe.register_hook("h1", "post-receive.sh")
        raw = pipe.encode_push_options({"user": "alice"})
        pipe.relay(raw, hook_id="h1")
        assert pipe.audit.size() == 1

    def test_relay_does_not_write_audit_when_rejected(self, tmp_hooks_root):
        pipe = self._build(tmp_hooks_root)
        raw = pipe.encode_push_options({"user": "bob"})
        pipe.relay(raw, hook_id="missing")
        assert pipe.audit.size() == 0

    def test_register_hook_returns_entry(self, tmp_hooks_root):
        pipe = self._build(tmp_hooks_root)
        entry = pipe.register_hook("h2", "post-receive.sh")
        assert entry.hook_id == "h2"
        assert entry.enabled is True
