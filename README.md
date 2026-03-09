# XED /TUI
> A mutt-style session browser for Claude Code — terminal-first, zero dependencies, no cloud.
> Deutsche Version: [de/README.md](de/README.md)

**Version:** v1.0.24 · **License:** MIT · **Org:** [Collective Context (CC)](https://collective-context.org)

---

## What is XED /TUI?

XED /TUI is a terminal browser for Claude Code sessions — inspired by mutt (email)
and ranger (file browser). It runs entirely locally, requires no API and no cloud service.

**Who needs it:** Anyone using Claude Code daily who wants to browse, annotate,
resume, and manage their sessions directly in the terminal.

---

## Installation

### Recommended — uv (fastest)
```bash
uv tool install xed-tui
```

### pip / pipx
```bash
pipx install xed-tui
# or:
pip install xed-tui
```

### One-line installer
```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

### From source
```bash
git clone https://github.com/XED-dev/TUI.git
cd TUI
python -m xed_tui
```

**Requirements:** Python 3.11+ · Unix terminal (Linux, macOS, WSL) · no pip packages needed

---

## Features — v1.0.24

- **4-Panel Layout** — Projects · Sessions · Reader · Notes (side-by-side)
- **Session Browser** — all `~/.claude/projects/` sorted by recency
- **Reader** — full transcript with Markdown rendering (`**bold**`, `` `code` ``, tables, code blocks)
- **`[a]` Resume** — start Claude Code with `--resume <uuid>` (CWD automatic)
- **`[r]` Clipboard** — `/resume <uuid>` → clipboard (for a running Claude Code)
- **`[e]` Notes** — per-session `memory/<uuid>.md`, editable in any editor
- **`[t]` Title** — rename sessions (syncs with Claude Code + ZED History)
- **`[/]` Search** — live search across titles and notes
- **`[#]` Tags** — label sessions, filter by tag (`/#hvd`)
- **`Ctrl+E`** — Settings: configure editor and default app
- **`Ctrl+R`** — hot-reload, state preserved via `--continue`
- **Multi-language help** — DE / EN / FR / JA / ES (`?` key)

---

## Quickstart

```bash
xed-tui                  # start
xed-tui --continue       # restore last state
xed-tui --help           # full keybinding reference
```

→ Full guide: [docs/quickstart.md](docs/quickstart.md)

---

## Keybindings

| Key | Action |
|-----|--------|
| `↑↓` / `j k` | Navigate |
| `Tab` / `← →` | Switch panel |
| `Enter` | Open session |
| `a` | Start Claude Code --resume |
| `r` | Resume command to clipboard |
| `e` | Open note in editor |
| `o` | Open note in default app |
| `t` | Set title |
| `/` | Live search |
| `#` | Set tags |
| `f` | Reader fullscreen |
| `n` | Notes fullscreen |
| `Ctrl+E` | Settings (editor, app) |
| `Ctrl+R` | Hot-reload |
| `?` | Help (5 languages) |
| `q` | Quit |

→ Full reference: [docs/keybindings.md](docs/keybindings.md)

---

## Why XED /TUI?

ZED and Claude Code have no built-in tool to **read, annotate, search and resume** sessions.
Sessions are stored as `.jsonl` files locally — human-readable, no lock-in.
XED /TUI is the browser for them.

---

## Contribute

All languages welcome · Alle Sprachen willkommen.

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

---

*Building XED /TUI @ Collective Context (CC) · License: MIT*
