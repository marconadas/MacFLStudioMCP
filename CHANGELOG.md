# Changelog

All notable changes to fLMCP are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

## [0.2.0] — 2026-09-01

Bridge protocol version: `0.4.0-browser-live-scorelog`.

### Added

- **Live metering** — `mixer_get_peaks(track)` / `mixer_all_peaks()` read L/R
  peak levels per mixer track during playback (>1.0 flags clipping);
  `channel_get_activity()` reads per-channel VU. Enables gain staging and
  "is this channel actually sounding?" checks without audio capture.
- **Per-step parameters** — `channel_get_step_params` / `channel_set_step_params`
  read/write graph-editor values (velocity, pan, pitch, fine pitch, release,
  mod X/Y, shift) per step, on top of the existing on/off grid bits.
- **Snap mode control** — `ui_get_snap_mode` / `ui_set_snap_mode` with named
  modes (`bar`, `beat`, `step`, `line`, `none`, …). Set snap before GUI-driven
  playlist edits so clicks land on the grid.
- **Browser navigation** — `browser_navigate` / `browser_focused` /
  `browser_tabs` / `browser_preview` / `browser_select`: walk the FL browser
  tree, audition samples/presets, and load them into the project without GUI
  clicks. (Classic tabs only — the FL Cloud "SOUNDS" tab is a webview with no
  scripting hooks.)
- **Performance mode** — `live_status` / `live_trigger` for live-clip
  launching when the playlist is in performance mode.
- **Score log** — `project_dump_score_log(seconds)` dumps recently played
  (unrecorded) notes into the selected pattern.
- **Misc** — `playlist_track_activity`, `pattern_groups`, `pattern_burn_loop`,
  `arrangement_selection`, `ui_focused_plugin`.

### Fixed

- Pin `mcp[cli]>=1.2.0,<2` — mcp 2.x removed `FastMCP` and breaks the server.
- Sanitize garbage peak values (e.g. `2.5e+27`) that FL returns for never-used
  mixer tracks.

### Known caveats

- The `shift` step parameter has odd semantics (reads return absolute tick
  offsets; writing can make a step's params read `-1`). Velocity/pan/pitch are
  reliable.
- FL's Python API still does not expose playlist clip placement/deletion or
  arrangement switching; those remain GUI-only.

## [0.1.0]

macOS port baseline (Calvin Williamson, from geezoria/FLStudioMCP): file-bus
bridge (FL's macOS interpreter blocks sockets/threads/subprocesses), ~130
actions across transport, patterns, channels, mixer, plugins, piano roll
(via `ComposeWithLLM.pyscript`), playlist, automation, project and UI, plus
voice-to-MIDI, audio analysis and DnB generators on the server side.
