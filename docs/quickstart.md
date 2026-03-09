# Quickstart — XED /TUI
> German version: [../de/docs/quickstart.md](../de/docs/quickstart.md)

## Requirements

- Python 3.11 or newer
- Claude Code installed and used at least once (creates `~/.claude/projects/`)
- Unix terminal: Linux, macOS, or WSL

## Installation

### Recommended — uv
```bash
uv tool install xed-tui
```

### pip / pipx
```bash
pipx install xed-tui
```

### npm (for Claude Code users)
```bash
npm install -g @xed-dev/tui
```

No additional `pip install` needed — stdlib only (`curses`).

## First launch

```bash
xed-tui
```

On first launch, XED /TUI automatically reads `~/.claude/projects/`.
You see your projects on the left and sessions to the right.

```
┌─ Projects ─┬─ Sessions ──────┬─ Reader ────────┬─ Notes ───┐
│ fb-data  3 │ #1  Mon  My ...  │ ▶ YOU           │ [notes]   │
│ github   1 │ #2  Fri  Bug ... │ question here   │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
 [?/H]Hlp [/]Find [#]Tag [T]Tit [D]Del [A]Agt [^E]Set ...
```

## First steps

1. `↑↓` — navigate through sessions
2. `Enter` — open and read a session
3. `a` — resume session in Claude Code
4. `e` — write a note for the session
5. `Ctrl+E` — configure your editor and default app
6. `?` — show all keybindings (5 languages)

## Restore last state

```bash
xed-tui --continue
```

State is saved automatically on quit and hot-reload (`Ctrl+R`).

## Next steps

→ [Keybindings](keybindings.md) · [Architecture](architecture.md)
