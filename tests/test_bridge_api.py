"""Bridge api.call / api.introspect dispatch, with FL's modules stubbed out."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

FL_MODULES = ["arrangement", "channels", "device", "general", "midi", "mixer",
              "patterns", "playlist", "plugins", "transport", "ui"]


@pytest.fixture()
def bridge(monkeypatch):
    for name in FL_MODULES:
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    sys.modules["general"].getVersion = lambda: 40
    sys.modules["mixer"].getTrackName = lambda i: "Insert %d" % i
    sys.modules["mixer"]._secret = lambda: "nope"
    path = Path(__file__).parent.parent / "fl_bridge" / "device_FLStudioMCP.py"
    spec = importlib.util.spec_from_file_location("fl_bridge_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_api_call_dispatches_public_functions(bridge):
    assert bridge._execute("api.call", {"module": "mixer", "fn": "getTrackName",
                                        "args": [3]}) == {"result": "Insert 3"}


@pytest.mark.parametrize("module,fn", [("mixer", "_secret"), ("os", "system"),
                                       ("mixer", "nope"), ("mixer", "")])
def test_api_call_rejects_private_unknown(bridge, module, fn):
    with pytest.raises(ValueError):
        bridge._execute("api.call", {"module": module, "fn": fn})


def test_api_introspect_lists_public_functions(bridge):
    r = bridge._execute("api.introspect", {})
    assert r["modules"]["mixer"] == ["getTrackName"]
    assert r["fl_api_version"] == 40
