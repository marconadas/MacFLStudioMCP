# cli-anything-flstudio

Agent-native CLI for FL Studio, built with the [CLI-Anything](https://github.com/HKUDS/CLI-Anything)
methodology. Every `fl-studio-mcp` tool becomes a shell command (`transport_set_tempo` →
`transport set-tempo --bpm 120`), so the CLI and the MCP server share one implementation:
the fLMCP bridge running inside FL Studio.

## Install

FL Studio is a hard dependency: install the fLMCP bridge first (`./install_mac.sh` in the repo root)
and enable the `fLMCP Bridge` controller in FL's MIDI settings.

From the repo root:

```bash
uv tool install --editable ./agent-harness --with-editable .
```

`fl-studio-mcp` must come from this checkout (`--with-editable .`): it is not on PyPI under our
name, and an unrelated package called `fl-studio-mcp` is.

## Use

```bash
cli-anything-flstudio --json fl ping                 # bridge online?
cli-anything-flstudio --json transport set-tempo --bpm 128
cli-anything-flstudio transport --help               # list a group's commands
cli-anything-flstudio                                # interactive REPL
```

Agents: see `skills/SKILL.md` (also linked into `~/.claude/skills/cli-anything-flstudio`).

## Tests

```bash
uv run --with pytest --with-editable ./agent-harness pytest agent-harness/cli_anything/flstudio/tests -v
```

`test_core.py` needs nothing; `test_full_e2e.py` needs FL Studio open with the bridge enabled
(set `CLI_ANYTHING_FORCE_INSTALLED=1` to test the installed command only). Plan and results: `tests/TEST.md`.
