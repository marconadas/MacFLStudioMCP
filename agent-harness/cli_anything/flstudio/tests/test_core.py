"""Unit tests: fl-studio-mcp tool registry -> Click commands. No FL Studio needed."""
from __future__ import annotations

import json
from types import SimpleNamespace

from click.testing import CliRunner

from cli_anything.flstudio.flstudio_cli import build_cli, split_name


class FakeToolManager:
    def __init__(self, tools):
        self.tools, self.calls = tools, []

    def list_tools(self):
        return self.tools

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "fl_fail":
            raise RuntimeError("bridge did not respond")
        if name == "fl_soft_fail":
            return {"ok": False, "error": "piano roll script not fired"}
        return {"tool": name, "args": arguments}


def tool(name, properties=None, required=()):
    return SimpleNamespace(name=name, description=f"{name} doc",
                           parameters={"properties": properties or {}, "required": list(required)})


TOOLS = [
    tool("transport_set_tempo", {"bpm": {"type": "number"}}, ["bpm"]),
    tool("plugin_name", {"index": {"type": "integer"},
                         "location": {"enum": ["channel", "mixer"], "type": "string", "default": "channel"}},
         ["index"]),
    tool("piano_roll_add_notes", {"notes": {"type": "array"},
                                  "channel": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": None}},
         ["notes"]),
    tool("ui_show_window", {"show": {"type": "boolean", "default": True}}),
    tool("fl_fail"),
    tool("fl_soft_fail"),
]


def run(args):
    tm = FakeToolManager(TOOLS)
    return CliRunner().invoke(build_cli(SimpleNamespace(_tool_manager=tm)), args), tm.calls


def test_split_name():
    assert split_name("transport_set_tempo") == ("transport", "set-tempo")
    assert split_name("piano_roll_add_notes") == ("piano-roll", "add-notes")
    assert split_name("fl_ping") == ("fl", "ping")


def test_number_option_and_json_output():
    r, calls = run(["--json", "transport", "set-tempo", "--bpm", "128.5"])
    assert r.exit_code == 0, r.output
    assert calls == [("transport_set_tempo", {"bpm": 128.5})]
    assert json.loads(r.output) == {"tool": "transport_set_tempo", "args": {"bpm": 128.5}}


def test_enum_default_and_required():
    assert run(["plugin", "name", "--index", "3"])[1] == [("plugin_name", {"index": 3, "location": "channel"})]
    assert run(["plugin", "name", "--index", "3", "--location", "bogus"])[0].exit_code != 0
    assert run(["plugin", "name"])[0].exit_code != 0  # --index is required


def test_json_array_and_unset_optional_dropped():
    r, calls = run(["piano-roll", "add-notes", "--notes", '[{"midi": 60}]'])
    assert calls == [("piano_roll_add_notes", {"notes": [{"midi": 60}]})], r.output
    assert run(["piano-roll", "add-notes", "--notes", "[oops"])[0].exit_code != 0


def test_bool_option():
    assert run(["ui", "show-window", "--show", "false"])[1] == [("ui_show_window", {"show": False})]


def test_tool_error_is_json_and_nonzero():
    r, _ = run(["--json", "fl", "fail"])
    assert r.exit_code == 1
    assert json.loads(r.output) == {"ok": False, "error": "bridge did not respond"}


def test_ok_false_result_exits_nonzero():
    r, _ = run(["--json", "fl", "soft-fail"])
    assert r.exit_code == 1
    assert json.loads(r.output) == {"ok": False, "error": "piano roll script not fired"}


def test_every_registry_tool_becomes_one_command():
    from fl_studio_mcp.server import build_app

    app = build_app()
    cli = build_cli(app)
    assert sum(len(g.commands) for g in cli.commands.values()) == len(app._tool_manager.list_tools())
