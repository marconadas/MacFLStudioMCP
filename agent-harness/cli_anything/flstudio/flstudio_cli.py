"""cli-anything-flstudio: drive FL Studio from the shell (agent-native, --json).

Every command is generated from the fl-studio-mcp tool registry, so the CLI and the
MCP server share one implementation: the fLMCP bridge running inside FL Studio.
`transport_set_tempo` becomes `transport set-tempo --bpm 120`. With no command, starts a REPL.
"""
from __future__ import annotations

import asyncio
import functools
import json
import os
import shlex

import click

from cli_anything.flstudio import __version__

GROUP_PREFIXES = ("piano_roll",)  # multi-word groups; other tool names split at the first "_"
_SCALARS = {"integer": click.INT, "number": click.FLOAT, "boolean": click.BOOL, "string": click.STRING}


class JSONParam(click.ParamType):
    name = "json"

    def convert(self, value, param, ctx):
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            self.fail(f"invalid JSON: {e}", param, ctx)


def split_name(tool_name: str) -> tuple[str, str]:
    """'transport_set_tempo' -> ('transport', 'set-tempo'); 'piano_roll_add_notes' -> ('piano-roll', 'add-notes')."""
    prefix = next((p for p in GROUP_PREFIXES if tool_name.startswith(p + "_")), tool_name.split("_", 1)[0])
    return prefix.replace("_", "-"), tool_name[len(prefix) + 1:].replace("_", "-")


def option_for(name: str, prop: dict, required: bool) -> click.Option:
    """Click option for one JSON-schema property of a tool."""
    schema = next((s for s in prop.get("anyOf", [prop]) if s.get("type") != "null"), prop)  # Optional[X] -> X
    if all(isinstance(v, str) for v in schema.get("enum") or [0]):
        ptype = click.Choice(schema["enum"])
    elif schema.get("type") in ("array", "object"):
        ptype = JSONParam()
    else:
        ptype = _SCALARS.get(schema.get("type"), click.STRING)
    # Click >= 8.3 treats an explicit default=None as "has a default", which disables `required`
    extra = {"default": prop["default"], "show_default": prop["default"] is not None} if "default" in prop else {}
    return click.Option(["--" + name.replace("_", "-"), name], type=ptype, required=required,
                        help=prop.get("description"), **extra)


def emit(data, as_json: bool) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, default=str, indent=None if as_json else 2))


def _call(tool, /, **kwargs) -> None:
    ctx = click.get_current_context()
    obj = ctx.find_root().obj
    args = {k: v for k, v in kwargs.items() if v is not None}  # unset optionals keep the tool's default
    try:
        result = asyncio.run(obj["app"]._tool_manager.call_tool(tool, args))
    except Exception as e:  # bridge offline, validation, FL-side error: agents need a clear message
        emit({"ok": False, "error": str(e)}, obj["json"])
        ctx.exit(1)
    emit(result, obj["json"])
    if isinstance(result, dict) and result.get("ok") is False:  # tools that report failure without raising
        ctx.exit(1)


def build_cli(app=None) -> click.Group:
    if app is None:
        os.environ.setdefault("FL_MCP_LOG_LEVEL", "WARNING")
        from fl_studio_mcp.server import build_app
        app = build_app()

    @click.group(invoke_without_command=True, help=__doc__)
    @click.option("--json", "as_json", is_flag=True, help="Compact JSON output (for agents).")
    @click.version_option(__version__)
    @click.pass_context
    def cli(ctx, as_json):
        ctx.ensure_object(dict).update(app=app, json=as_json)
        if ctx.invoked_subcommand is None and not ctx.obj.get("in_repl"):
            repl(cli)

    groups: dict[str, click.Group] = {}
    for tool in app._tool_manager.list_tools():
        gname, cname = split_name(tool.name)
        if gname not in groups:
            groups[gname] = click.Group(gname, help=f"{gname} commands")
            cli.add_command(groups[gname])
        required = set(tool.parameters.get("required", []))
        groups[gname].add_command(click.Command(
            cname, callback=functools.partial(_call, tool.name), help=(tool.description or "").strip(),
            params=[option_for(n, p, n in required) for n, p in tool.parameters.get("properties", {}).items()]))
    return cli


def repl(cli: click.Group) -> None:
    from cli_anything.flstudio.utils.repl_skin import ReplSkin

    skin = ReplSkin("flstudio", version=__version__)
    # vendored skin defaults to the HKUDS registry; this harness lives in MacFLStudioMCP
    skin.display_name = "FL Studio"
    skin.skill_install_cmd = "uv tool install -e agent-harness --with-editable .  (MacFLStudioMCP repo)"
    skin.global_skill_path = os.path.expanduser("~/.claude/skills/cli-anything-flstudio/SKILL.md")
    skin.print_banner()
    session = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(session).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line in ("exit", "quit"):
            break
        if not line:
            continue
        try:
            cli.main(shlex.split(line), prog_name="", standalone_mode=False, obj={"in_repl": True})
        except click.exceptions.Exit:
            pass
        except (click.ClickException, ValueError) as e:  # ValueError: unbalanced quotes from shlex
            skin.error(e.format_message() if isinstance(e, click.ClickException) else str(e))
    skin.print_goodbye()


def main() -> None:
    build_cli()(prog_name="cli-anything-flstudio")


if __name__ == "__main__":
    main()
