# Quickstart — XED /TUI
> German source: `../de/docs/quickstart.md`

## Requirements

- Python 3.8 or newer
- Claude Code installed and set up
- At least one Claude Code session exists

## Installation

```bash
git clone https://github.com/XED-dev/TUI.git
cd TUI
python src/xed-tui_v1.py
```

No `pip install` needed — stdlib only (`curses`).

## First launch

On first launch, XED /TUI automatically reads `~/.claude/projects/`.
You see your projects on the left and sessions to the right.

```
┌─ Projects ─┬─ Sessions ──────┬─ Reader ────────┬─ Notes ───┐
│ fb-data    │ Session 1       │ [content]       │ [notes]   │
│ github.io  │ Session 2       │                 │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
```

## First steps

1. `↑↓` — navigate through sessions
2. `Enter` — open and read a session
3. `a` — resume session in Claude Code
4. `e` — write a note for the session
5. `?` — show all keybindings

## Next steps

→ [Keybindings](keybindings.md) · [Architecture](architecture.md)
