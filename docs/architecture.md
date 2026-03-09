# Architecture — XED /TUI
> German source: [../de/docs/architecture.md](../de/docs/architecture.md)

## Overview

XED /TUI is written in pure Python — stdlib only, no dependencies.

```
src/xed_tui/xed-tui_v1.py   (~2400 lines)
├── State layer      — read/write sessions, projects, continue-state
├── Parser layer     — parse JSONL, render inline Markdown
├── Layout layer     — manage 4 curses panels
└── Key dispatch     — keyboard input → actions
```

## Data sources

```
~/.claude/projects/<slug>/
├── <uuid>.jsonl          ← Session transcript (one line = one JSON object)
├── memory/
│   ├── MEMORY.md         ← Persistent memory (auto-loaded by Claude Code)
│   ├── titles.json       ← Custom titles (written by XED /TUI)
│   └── <uuid>.md         ← Session notes
└── ~/.local/share/xed-tui/continue.json  ← UI state for hot-reload
```

## v1 vs. v2 (Roadmap)

| Component | v1 (curses) | v2 (urwid, planned) |
|---|---|---|
| Layout | `curses.newwin()`, manual | `urwid.Columns` / `urwid.Pile` |
| Mouse | ❌ | `mouse_event()` native |
| Rendering | full redraw on change | diffs only (canvas-diff) |
| Key dispatch | if-elif chain | dispatch table |
| Async | ❌ | `urwid.AsyncioEventLoop` |

## Development workflow

Daily development: `fb-data/scripts/bin/XED-TUI/xed-tui_v1.py`
Release sync: → `xed/src/xed_tui/xed-tui_v1.py` at milestones
