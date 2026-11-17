# FL Studio — CLI-Anything analysis (SOP)

## Backend

FL Studio is closed source, so there is no engine library to wrap. The backend is FL's own
embedded Python scripting API (modules `channels`, `mixer`, `patterns`, `playlist`, `transport`,
`ui`, `general`, `plugins`, `arrangement`, `device`; API v45 on FL 26.1.7), reached through the
**fLMCP bridge** (`fl_bridge/device_FLStudioMCP.py`): a MIDI controller script that polls a file bus
(`Settings/Hardware/fLMCP Bridge/bus/req_*.json` → `resp_*.json`) from FL's `OnIdle`, because
FL's macOS sub-interpreter blocks sockets, threads and subprocesses.

## Data model

The state is the **live FL session**. FL 2026 `.flp` files are binary and `pyflp` cannot parse
them, so the CLI never edits project files: it reads and mutates the open project through the
scripting API, and FL's own undo history records the changes (`project undo`).

## GUI → API mapping

The ~170 `fl-studio-mcp` tools are the mapping (one tool per GUI action). This harness does not
duplicate them: `flstudio_cli.py` generates one Click command per tool from the MCP tool registry
(name, JSON schema, docstring), so the CLI cannot drift from the MCP server. `fl api-introspect`
lists every scripting function of the running build and `fl api-call` reaches the ones no tool wraps.

## What the scripting API cannot do (and the workaround)

| GUI action | Status |
|------------|--------|
| Load an instrument | native macOS `Add` menu via System Events (`channel add-plugin`; needs Accessibility) |
| Write piano-roll notes | piano-roll script `ComposeWithLLM` fired from the piano roll (see repo docs) |
| Render to audio | not possible from scripts; user presses Ctrl+R |
| Delete a pattern | not in the API; `pattern delete` renames it to empty |

FL's internal `ilmcp` module (used by FL's Gopher assistant for adding plugins/effects) is
registered only in Gopher's interpreter and is not importable from controller scripts.

## Session / undo

No CLI session file: FL holds the state, so there is nothing to save between commands and the
cli-anything auto-save rule does not apply. Undo/redo use FL's history (`project undo`, `project redo`).
