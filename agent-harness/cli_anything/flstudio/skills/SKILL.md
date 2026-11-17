---
name: cli-anything-flstudio
description: Operate the running FL Studio from the shell with `cli-anything-flstudio` (transport, channels, mixer, patterns, piano roll, playlist, plugins, project, raw scripting API). Use when asked to control, inspect or edit an open FL Studio session.
---

# cli-anything-flstudio

Agent-native CLI for FL Studio on macOS. Every command maps 1:1 to an `fl-studio-mcp` tool and
runs inside FL through the fLMCP bridge, so it acts on the **live, open project**.

## Prerequisites

- FL Studio running, with a MIDI input row set to controller type **fLMCP Bridge**.
- Check first: `cli-anything-flstudio --json fl ping` → `midi_bridge.online` must be `true`.

## Usage

```bash
cli-anything-flstudio --json <group> <command> [--option value ...]
cli-anything-flstudio <group> --help          # commands of a group
cli-anything-flstudio <group> <command> --help  # options of a command
```

- Always pass `--json`, right after the command name (`cli-anything-flstudio --json transport status`;
  `transport status --json` is a usage error). Output is one compact JSON line on stdout.
- Failure: exit code 1 and a JSON object with `"ok": false` (plus `error`, or the tool's own details).
  Read it before retrying.
- Usage errors (unknown command, missing/invalid option, bad JSON value) exit 2 with plain text on stderr.
- Lists/objects are JSON strings: `--notes '[{"midi":60,"time":0,"duration":1,"velocity":0.8}]'`.
- Booleans take a value: `--show true`.
- The user may be editing FL at the same time: read state (`status`, `list`, `all`) before mutating.

## Command groups

| Group | Commands |
|-------|----------|
| `transport` | play, stop, record, status, set-tempo, set-position, set-loop-mode, set-time-signature, jog, song-length, ... |
| `pattern` | list, current, create, rename, select, clone, set-length, set-color, find-by-name, groups, burn-loop, ... |
| `channel` | all, info, select, set-volume, set-pan, set-pitch, mute, solo, set-name, route-to-mixer, set-step-sequence, get-step-params, trigger-note, add-plugin, ... |
| `mixer` | all-tracks, track-info, set-volume, set-pan, mute, solo, route, set-send-level, set-eq-band, get-peaks, all-peaks, fx-slots, ... |
| `plugin` | name, params, find-param, get-param, set-param, set-preset, next-preset, list-mixer-track, show-editor, ... |
| `piano-roll` | read, add-notes, add-chord, add-arpeggio, clear, quantize, transpose, humanize, write-pattern(s), status, ... |
| `playlist` | all-tracks, track-info, list-clips, place-pattern, delete-clip, add-marker, list-markers, set-track-name, ... |
| `arrangement` | list, current, select, jump-marker, play-time, selection |
| `automation` | record-tempo, record-channel-volume, record-channel-pan, record-mixer-volume, record-plugin-param |
| `project` | metadata, version, save, save-as, new, open, undo, redo, undo-history, dump-score-log, render (stub) |
| `ui` | show-window, hide-window, focused-window, set-snap-mode, get-snap-mode, hint, ... |
| `browser`, `live` | browser navigation/preview; performance-mode clips |
| `fl` | ping, bridge-info, **api-introspect**, **api-call**, call-raw, reconnect |

## Examples

```bash
cli-anything-flstudio --json transport status
cli-anything-flstudio --json transport set-tempo --bpm 128
cli-anything-flstudio --json pattern create --name "Verse drums"
cli-anything-flstudio --json channel set-step-sequence --index 0 --steps '[1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0]'
cli-anything-flstudio --json mixer set-volume --track 1 --volume 0.8
cli-anything-flstudio --json fl api-introspect                     # every scripting function FL exposes
cli-anything-flstudio --json fl api-call --module mixer --fn getTrackName --args '[1]'
```

## Limits (verified on FL 26.1.7)

- `project render` cannot render (FL's script API has no render; the user must press Ctrl+R).
- `channel add-plugin` presses FL's native `Add` menu: it needs macOS Accessibility permission for the
  host app, otherwise it returns error -1719 and changes nothing.
- Piano-roll writes need FL's `ComposeWithLLM` piano-roll script to be fired once per FL session.
- `pattern delete` only renames the pattern to empty (FL's API has no delete).
- Anything not wrapped by a command: `fl api-introspect`, then `fl api-call`.
