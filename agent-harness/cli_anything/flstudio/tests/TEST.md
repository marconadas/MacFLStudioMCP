# cli-anything-flstudio — test plan and results

## Test inventory

| File | Kind | Needs FL Studio | Planned |
|------|------|-----------------|---------|
| `test_core.py` | unit: registry → Click adapter, fake tool manager | no | 8 |
| `test_full_e2e.py` | E2E: installed `cli-anything-flstudio` against the real FL Studio | **yes** | 5 |

## Unit plan (`test_core.py`)

The CLI has one module, `flstudio_cli.py`, and it holds no FL logic: it turns each
fl-studio-mcp tool into a Click command. Tests cover that conversion with a fake tool manager:

- `split_name`: `transport_set_tempo` → `transport set-tempo`, multi-word `piano_roll_*` group, `fl_ping`.
- Number option + `--json` output: values arrive typed (`--bpm 128.5` → `128.5`), output is one JSON line.
- Enum (`Literal`) → `click.Choice` with the schema default; required options are enforced.
- `array` → JSON-parsed option; unset `Optional` options are dropped so the tool default applies; bad JSON fails.
- `boolean` option (`--show false`).
- Tool exception → `{"ok": false, "error": ...}` and exit code 1 (agents must see failures).
- Tool that returns `{"ok": false, ...}` without raising → exit code 1 too (added after code review).
- Every real tool in the fl-studio-mcp registry becomes exactly one command (schema coverage).

## E2E plan (`test_full_e2e.py`)

No graceful degradation (cli-anything rule): FL Studio must be running with the
`fLMCP Bridge` controller enabled, otherwise these tests fail. Every call goes through the
**installed** command via `_resolve_cli("cli-anything-flstudio")` (set
`CLI_ANYTHING_FORCE_INSTALLED=1` to forbid the `python -m` fallback).

- `--help` lists the command groups.
- `fl ping` → the MIDI bridge is online.
- `fl api-introspect` → the live scripting API surface includes `mixer.getTrackPeaks`.
- Workflow **tempo round trip** (simulates "set the session tempo"): read BPM → `transport set-tempo` to BPM+1 →
  verify via `transport status` → restore → verify restored.
- Workflow **channel rename round trip** (simulates "label an instrument"): read channel 0's name →
  `channel set-name` → verify with `channel info` → restore the original name. (Channel 0 always exists;
  renaming pattern 1 in an empty project would create the pattern, which cannot be undone via the API.)

Both mutations are reverted in `finally` blocks, so the open project ends unchanged
(FL's undo history still records them).

## Known gaps

- **No rendered-audio E2E.** FL's scripting API cannot render; `project render` is a stub that asks the
  user for Ctrl+R, and the macOS build shows no command-line render mode. Output verification is
  therefore done on live FL state, not on exported files.
- `channel add-plugin` needs macOS Accessibility permission for the host app (native `Add` menu);
  it is not exercised here.
- Piano-roll writes need FL's piano-roll script to be fired (see the repo README); not exercised here.

## Results

Run on 2026-11-17, FL Studio 26.1.7 (API v45), bridge `0.5.0-api`, empty project open,
`CLI_ANYTHING_FORCE_INSTALLED=1`, user-level install first on `PATH`
(`[_resolve_cli] Using installed command: ~/.local/bin/cli-anything-flstudio`):

```
test_core.py::test_split_name PASSED
test_core.py::test_number_option_and_json_output PASSED
test_core.py::test_enum_default_and_required PASSED
test_core.py::test_json_array_and_unset_optional_dropped PASSED
test_core.py::test_bool_option PASSED
test_core.py::test_tool_error_is_json_and_nonzero PASSED
test_core.py::test_ok_false_result_exits_nonzero PASSED
test_core.py::test_every_registry_tool_becomes_one_command PASSED
test_full_e2e.py::test_help_lists_groups PASSED
test_full_e2e.py::test_bridge_online PASSED
test_full_e2e.py::test_introspect_lists_live_api PASSED
test_full_e2e.py::test_tempo_round_trip PASSED        (tempo 140.0 -> 141.0 -> 140.0 BPM)
test_full_e2e.py::test_channel_rename_round_trip PASSED
13 passed in 8.82s
```

After the run the project was unchanged (tempo 140.0, channel 0 `Sampler`).

Summary: 13/13 (100%), unit 8 + E2E 5. Coverage notes: see "Known gaps" (no audio render,
`channel add-plugin` and piano-roll writes not exercised).
