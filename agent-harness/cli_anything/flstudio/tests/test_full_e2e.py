"""E2E against the real FL Studio via the installed `cli-anything-flstudio` command.

Requires FL Studio running with the `fLMCP Bridge` controller enabled. No graceful
degradation (cli-anything rule): with FL closed these tests fail. Mutations are reverted.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys


def _resolve_cli(name):
    """Installed command, or `python -m` fallback; CLI_ANYTHING_FORCE_INSTALLED=1 forbids the fallback."""
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1":
        raise RuntimeError(f"{name} not found in PATH. Install with: uv tool install -e agent-harness --with-editable .")
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m cli_anything.flstudio")
    return [sys.executable, "-m", "cli_anything.flstudio"]


CLI = _resolve_cli("cli-anything-flstudio")


def fl(*args):
    r = subprocess.run(CLI + ["--json", *args], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


def test_help_lists_groups():
    r = subprocess.run(CLI + ["--help"], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    for group in ("transport", "mixer", "channel", "piano-roll"):
        assert group in r.stdout


def test_bridge_online():
    assert fl("fl", "ping")["midi_bridge"]["online"] is True


def test_introspect_lists_live_api():
    mods = fl("fl", "api-introspect")["modules"]
    assert {"mixer", "channels", "transport"} <= set(mods)
    assert "getTrackPeaks" in mods["mixer"]


def test_tempo_round_trip():
    before = fl("transport", "status")["bpm"]
    try:
        fl("transport", "set-tempo", "--bpm", str(before + 1))
        assert abs(fl("transport", "status")["bpm"] - (before + 1)) < 0.01
    finally:
        fl("transport", "set-tempo", "--bpm", str(before))
    assert abs(fl("transport", "status")["bpm"] - before) < 0.01
    print(f"\n  tempo {before} -> {before + 1} -> {before} BPM")


def test_channel_rename_round_trip():
    # channel 0 always exists (renaming pattern 1 in an empty project would create it: not reversible)
    original = fl("channel", "info", "--index", "0")["name"]
    label = "cli-anything e2e"
    try:
        fl("channel", "set-name", "--index", "0", "--name", label)
        assert fl("channel", "info", "--index", "0")["name"] == label
    finally:
        fl("channel", "set-name", "--index", "0", "--name", original)
    assert fl("channel", "info", "--index", "0")["name"] == original
