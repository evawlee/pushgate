import os
import pytest

from pushgate.registry.hook_registry import HookRegistry


@pytest.fixture(autouse=True)
def _reset_hook_registry():
    HookRegistry._resolved_hooks = {}
    HookRegistry._registered_paths = []
    yield


@pytest.fixture
def tmp_hooks_root(tmp_path):
    root = tmp_path / "hooks"
    root.mkdir()
    pre = root / "pre-receive"
    pre.write_text("ok pre")
    post = root / "post-receive.sh"
    post.write_text("ok post")
    return str(root)


@pytest.fixture
def tmp_sibling_dir(tmp_path):
    sib = tmp_path / "secrets"
    sib.mkdir()
    secret = sib / "passwd"
    secret.write_text("root:x:0:0:root:/root:/bin/sh")
    return str(sib)
