# Changelog
> German version: [de/CHANGELOG.md](de/CHANGELOG.md)

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: `MAJOR.MINOR`

---

## [1.0.23] — unreleased

### Changed
- Versioning switched to 3-part semver (`MAJOR.MINOR.PATCH`) — previous `1.022` was normalized to `1.22` by PyPI (PEP 440), causing mismatches in Homebrew and install commands

## [1.22] — 2026-03-09
*Previously tagged as `v1.022` — PyPI normalized the version.*

### Added
- `Ctrl+E` — Settings overlay: configure editor (`auto` / `msedit` / `nano` / custom) and default app (`auto` / `typora` / custom)
- `[E]` respects `editor_pref` setting; `[O]` respects `open_pref` setting
- Settings persisted in `continue.json` across sessions and hot-reloads
- Help texts updated in all 5 languages (DE / EN / FR / JA / ES)
- Status bar: `[^E]Set` shortcut hint

## [1.021] — 2026-03-07

### Added
- Multi-language help overlay (DE / EN / FR / JA / ES), switchable with `←→` or number keys `1–5`
- Language preference persisted in `continue.json`

## [1.020] — 2026-03-06

### Added
- `[#]` Tags: per-session labels stored in `memory/tags.json`
- Tag filter: `/#tag` in search mode filters sessions by tag
- Token counter: `output_tokens` displayed as `42k` in sessions panel

## [1.018] — 2026-03-05

### Fixed
- Empty reader panel on startup when saved `focus != "threads"` (explicit `preview_reader()` before event loop)

## [1.017] — 2026-03-04

### Fixed
- `flush_table()`: column widths via visible length, ignoring Markdown markers

## [1.016] — 2026-03-03

### Added
- Markdown table rendering with box-drawing: `┌─┬─┐` / `│ cell │` / `└─┴─┘`
- `A_ITALIC` with ncurses 6.1+ fallback to underline

## [1.010] — 2026-02-28

### Added
- `--continue` / `Ctrl+R`: full state persisted to `~/.local/share/xed-tui/continue.json`
- Markdown rendering: h1/h2/h3, bold, inline code, italic, hrule, code blocks, tables, blockquotes
- Token counter, full-text search `[/]`, Notes-Sync (`.sync` sidecar)
- `[a]` Agent launch, `[r]` Resume-to-clipboard, Unicode input via `get_wch()`

## [1.001] — 2026-02-20

### Added
- Initial release: 4-panel curses TUI for Claude Code sessions (`~/.claude/projects/`)
- Projects, Sessions, Reader (JSONL → Markdown), Notes panels
- vim-style navigation, `[t]` title, `[d]` delete, `[e]` editor, `[c]` clipboard
- New note prefill with session transcript + `.sync` sidecar

---

*Development history: [fb-data](https://github.com/edikte/fb-data/commits/main/scripts/bin/XED-TUI/)*
