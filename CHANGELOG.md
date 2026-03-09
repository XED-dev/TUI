# Changelog — XED /TUI
> German source: `de/CHANGELOG.md` — this file is an AI translation.
> Format: [Keep a Changelog](https://keepachangelog.com/) · [Semantic Versioning](https://semver.org/)

---

## [v1.018] — 2026-03-09

### First public release

**Added:**
- 4-panel layout: Projects · Sessions · Reader · Notes
- Full Markdown rendering (bold, italic, code, tables with box-drawing)
- `[a]` Start Claude Code `--resume` directly from the TUI
- `[r]` Copy `/resume <uuid>` to clipboard
- `[e]` Edit session notes in `$EDITOR`
- `[t]` Rename sessions (native JSONL, compatible with ZED History)
- `[/]` Live search across all sessions
- `Ctrl+R` Hot-reload (state preserved via `--continue`)
- Startup preview: last state restored on launch

**Fixed:**
- v1.016: `draw_table_row()` wrote hardcoded ASCII `|` instead of Unicode `│`
- v1.017: Table column widths based on Markdown length instead of visual length
- v1.018: Empty preview panel on startup when `focus != "threads"`

**Technical:**
- ~1800 lines of pure Python · stdlib only (`curses`) · no dependencies
- `CONTINUE_STATE_PATH`: `~/.local/share/xed-tui/continue.json`

---

*Older development history: [fb-data](https://github.com/edikte/fb-data/commits/main/scripts/bin/XED-TUI/)*
