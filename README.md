# XED /TUI

**Browse, search and resume your Claude Code sessions — right in the terminal.**

> 🇩🇪 Deutsche Version: [de/README.md](https://github.com/XED-dev/TUI/blob/main/de/README.md)

![XED /TUI — 4-Panel Session Browser](https://raw.githubusercontent.com/XED-dev/TUI/main/docs/images/hero.png)

## Install

```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

Or: `pipx install xed-tui` · `uv tool install xed-tui` · `brew install xed-dev/xed/xed-tui`

Requires: [Claude Code](https://code.claude.com) installed · Python 3.11+ · Linux, macOS, or WSL

## 30-Second Demo

```bash
xed-tui          # browse all sessions
↑↓  Enter        # navigate and read
/schema           # search across everything
a                 # resume in Claude Code
e                 # write a note
?                 # help (DE/EN/FR/JA/ES)
```

## Why XED /TUI?

| | XED /TUI | Alternatives |
|---|---|---|
| **Dependencies** | ✅ None (Python stdlib) | Go compiler / Node.js |
| **Per-session notes** | ✅ Smart sync | Not available |
| **Markdown rendering** | ✅ Bold, code, tables | Raw text |
| **Multi-language** | ✅ 5 languages | English only |
| **Install time** | ✅ ~5 seconds | Compile required |

---

## Features

- **4-Panel Layout** — Projects · Sessions · Reader · Notes
- **`a` Resume** — start Claude Code with `--resume <uuid>` (CWD automatic)
- **`r` Clipboard** — copy `/resume <uuid>` for a running Claude Code instance
- **`e` Notes** — per-session notes with auto-sync
- **`/` Search** — live full-text search across titles and notes
- **`#` Tags** — label sessions, filter by tag (`/#bugfix`)
- **`Ctrl+R`** — hot-reload, state preserved
- **Multi-language help** — DE / EN / FR / JA / ES

→ Full documentation: [Wiki](https://github.com/XED-dev/TUI/wiki) ·
[Quickstart](https://github.com/XED-dev/TUI/wiki/Installation-EN) ·
[Keybindings](https://github.com/XED-dev/TUI/wiki/Keybindings-EN)

→ Landing page: [tui.xed.dev](https://tui.xed.dev) ·
XED Suite: [xed.dev](https://xed.dev)

---

## Keybindings

| Key | Action |
|---|---|
| `↑↓` / `j k` | Navigate |
| `Tab` / `← →` | Switch panel |
| `Enter` | Open session |
| `a` | Resume in Claude Code |
| `e` | Edit note |
| `/` | Search |
| `#` | Tags |
| `f` / `n` / `m` | Fullscreen / Notes / Swap |
| `?` | Help (5 languages) |
| `q` | Quit |

→ [All keybindings](https://github.com/XED-dev/TUI/wiki/Keybindings-EN)

---

## Contribute

All languages welcome.
→ [CONTRIBUTING.md](https://github.com/XED-dev/TUI/blob/main/CONTRIBUTING.md) ·
[Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

*[Collective Context](https://collective-context.org) · MIT License*
