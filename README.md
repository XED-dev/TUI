# XED /TUI
> A mutt-style session browser for Claude Code — terminal-first, no cloud service.
> German source: `de/README.md` — this file is an AI translation.

**Organisation:** [Collective Context (CC)](https://collective-context.org) ·
**License:** MIT · **Version:** v1.018

---

## What is XED /TUI?

XED /TUI is a terminal browser for Claude Code sessions — inspired by mutt (email)
and ranger (file browser). It runs entirely locally, requires no API and no cloud service.

**Who needs it:** Anyone using Claude Code daily who wants to browse, annotate,
resume or manage their sessions — directly in the terminal.

---

## Installation

```bash
# Requirements: Python 3.8+ (stdlib only, no pip packages needed)
git clone https://github.com/XED-dev/TUI.git
cd TUI

# Start
python src/xed-tui_v1.py
```

---

## Features — v1.018

- **4-Panel Layout** — Projects · Sessions · Reader · Notes (side-by-side)
- **Session Browser** — all `~/.claude/projects/` sorted by time
- **Reader** — full transcript with Markdown rendering
  (`**bold**`, `` `code` ``, `*italic*`, tables, code blocks, quotes)
- **`[a]` Resume** — start Claude Code with `--resume <uuid>` directly (CWD automatic)
- **`[r]` Clipboard** — `/resume <uuid>` → clipboard (for a running Claude Code)
- **`[e]` Notes** — per-session `memory/<uuid>.md`, editable in `$EDITOR`
- **`[t]` Title** — rename sessions (appears in Claude Code + ZED History)
- **`[/]` Search** — live search across all sessions
- **`Ctrl+R`** — hot-reload without restart

---

## Keybindings

| Key | Action |
|---|---|
| `↑↓` / `j k` | Navigate |
| `Tab` | Switch panel |
| `Enter` | Open session |
| `a` | Start Claude Code --resume |
| `r` | Resume command to clipboard |
| `e` | Open note in editor |
| `t` | Set title |
| `/` | Live search |
| `f` | Reader fullscreen |
| `n` | Notes fullscreen |
| `Ctrl+R` | Hot-reload |
| `?` | Help |
| `q` | Quit |

→ Full reference: [docs/keybindings.md](docs/keybindings.md)

---

## Why XED /TUI?

ZED shows Claude Code sessions in its History panel — but there is no tool to
**read, annotate, search and resume** them — until XED /TUI.

Sessions are stored as `.jsonl` files locally — human-readable, no lock-in.
XED /TUI is the browser for them.

---

## Contribute

All languages welcome · Alle Sprachen willkommen.

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

---

*Building XED /TUI @ Collective Context (CC) · License: MIT*
