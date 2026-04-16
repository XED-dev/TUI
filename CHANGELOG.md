# Changelog
> German version: [de/CHANGELOG.md](de/CHANGELOG.md)

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: `MAJOR.MINOR`

---

## [1.26.6] — 2026-04-16

### Fixed
- **`get_session_cwd()` now validates the cwd against the JSONL project slug before returning it.** Claude Code logs cwd changes into `isMeta` records as the session's shell wanders (e.g. a `cd git/xed/` during a build). The naive „first `isMeta`+cwd wins" heuristic returned the wrong directory for sessions that had moved between projects — AG006 got `/mnt/.../git/xed` instead of `/mnt/.../fb-data` after multiple cross-project operations. `os.chdir` to the wrong cwd made Claude Code look for the session in `~/.claude/projects/-mnt-…-xed/` where it doesn't exist → „No conversations found to resume". v1.26.6 only returns a cwd whose slug (Claude convention: `/` → `-`) equals the JSONL parent directory name. Sessions without a matching record fall back to `None` (no `chdir`), so the user's shell cwd stays in effect — safer than wandering off.

## [1.26.5] — 2026-04-16

### Fixed
- **`xed-tui claude <pattern>` now passes the user pattern to `claude --resume`, not the full title.** v1.26.4 passed the full resolved custom-title, but Claude Code v2.x fails with `No conversations found to resume` for sessions that have accumulated many `custom-title` records (44+ after repeated `[U]` repair runs) or complex titles with special chars (`/`, etc.). The only reliable mechanism is to pass a short pattern and let Claude open its resume picker pre-filtered — one Enter press completes the resume. XED still resolves the unique match internally; the title goes to stderr as verification. Trade-off: one extra keystroke in exchange for robustness against Claude's v2.x resolution quirks.

## [1.26.4] — 2026-04-16

### Fixed
- **`xed-tui claude <title>` now passes the title to `claude --resume`, not the UUID.** Claude Code v2.x treats the `--resume` argument as the custom-title / session_name — UUID-resume fails on sessions with multiple `custom-title` records (which every session has after a `[U]` run with v1.26.1's `repair_custom_title_format`). Error was `No conversation found with session ID: <uuid>`. v1.26.4 passes the full title string that XED already resolved, which Claude handles cleanly. Bonus: if a user types `claude --resume "AG006"` directly (short prefix, not unique), Claude v2.x opens the interactive picker pre-filtered — useful fallback for ambiguous patterns.

## [1.26.3] — 2026-04-15

### Added
- **`xed-tui claude <title-pattern>` CLI subcommand** — finds a live session by title (case-insensitive substring) across all projects and replaces the Python process with `claude --resume <uuid>` in the correct `cwd`. Title resolution follows the same priority as the TUI (native `custom-title` in JSONL → `titles.json` → first human message). On multiple matches: lists candidates on stderr and exits 2. On zero matches: exits 1 with a hint about `[L]` Lend for archive-only sessions.
- Convention: titles in our workflow always start with `"AA000"` to `"ZZ999"` (5 chars = 2 letters + 3 digits, e.g. `AG006`, `AI022`). This 5-char prefix is usually enough to identify a session uniquely — `xed-tui claude AG006` resumes the session, no UUID typing required.

## [1.26.2] — 2026-04-15

### Fixed
- **Title stale after restart when a session has an older archive copy.** `title()` resolved the native `custom-title` via `resolved_jsonl()`, which is archive-preferred. When XED renamed a session after the last archive snapshot, the archive kept the old `custom-title` — on next XED start the archive won again and the old label reappeared in both the normal project list and the `★ ARCHIV` view. v1.26.2 reads the native title from the **live** JSONL whenever it exists (source of truth for current renames) and only falls back to the archive for orphaned sessions. Content-reader paths (`first_human_title`, `_build_reader_lines`) stay archive-preferred for 90-day-cleanup resilience.

## [1.26.1] — 2026-04-15

### Fixed
- **`custom-title` records now written in compact Claude-native format.** XED previously used Python's default `json.dumps` which adds whitespace padding (`{"type": "custom-title", …}`). Claude Code's and ZED's History / Resume UIs parse session labels with whitespace-sensitive patterns and silently ignored XED-written records — XED-renamed sessions appeared in those UIs under the first user message instead of the new title. v1.26.1 writes with `separators=(",", ":")` (`{"type":"custom-title",…}`), bit-identical to what Claude itself writes.
- **`[U]` batch update retrofits pre-v1.26.1 sessions.** `repair_custom_title_format()` appends a compact rewrite of the most recent title to every JSONL whose last `custom-title` record is still whitespace-padded. Idempotent, append-only, non-destructive — runs automatically in `[U]` and reports `N Titel repariert` in the status line. Sessions never touched by `[U]` stay as-is; a single `[T]` rename also produces the new format.

## [1.26.0] — 2026-04-15

### Added
- **Note co-archiving (M0)** — on `[e]` / `[E]` / `[u]` / `[U]`, the per-session note `<uuid>.md` is now copied into `~/.xed/tui/archive/<proj>/<uuid>.md` alongside the JSONL. The note is the curated catalog card — it now survives alongside the volume.
- **`[L]` Lend restores the note too** — if an archived `<uuid>.md` exists, it's restored to `memory/<uuid>.md` next to the JSONL. Status message shows `Ausgeliehen + Notiz:` when both came back.
- **Stats line in `★ ARCHIV`** — single-line summary at the top of the sessions panel: volumes · catalog cards · total bytes · date range · top project. No database, just `os.stat()` — scales comfortably into the thousands.
- **Ranked search with context snippets** — `/` filters now score hits (title match weighs 10×, note match 1×) and sort by relevance. When a note hit isn't in the title, a short `«…snippet…»` is appended to the session row.

### Changed
- **Sidecar migration (M1–M4)** — XED-specific sidecars leave `~/.claude/projects/<proj>/memory/` and settle into `~/.xed/tui/state/`:
  - `continue.json` → `~/.xed/tui/state/continue.json` (was `~/.local/share/xed-tui/`)
  - `titles.json` / `tags.json` → `~/.xed/tui/state/<proj>/`
  - `<uuid>.sync` → `~/.xed/tui/state/<proj>/<uuid>.sync`
  - Per-session note `<uuid>.md` **stays** in `memory/` — it's the bridge to Claude's auto-memory.
  - External tools (Claude Code, ZED) were never affected: the title source-of-truth is the `custom-title` record in the JSONL itself, not `titles.json`.
- **Lazy migration** — readers fall back to the legacy paths if the new location is empty, so nothing breaks on upgrade. Writes always go to the new home.

### Docs
- README gets a **Backup** section pointing at Syncthing / rsync / git-annex — XED /TUI ships no sync on purpose.

## [1.25.0] — 2026-04-14

### Added
- **Virtual `★ ARCHIV` project** at the top of the project panel — browse all notes across all projects, including orphaned ones whose source sessions Claude Code has already cleaned up
- **XED library at `~/.xed/tui/archive/<proj>/<uuid>.jsonl`** — shadow copies of Claude Code sessions, survive Claude's retention cleanup
- **Auto-archiving** on `[e]` / `[E]` (edit note) and `[u]` / `[U]` (update note) — every curation act preserves the source session
- **`[U]` batch update** — update/create all notes in the current project in one pass (N new · N refreshed · N archived)
- **`[L]` Lend** — restore an archived session back into `~/.claude/projects/<proj>/` with fresh mtime (resets Claude Code's cleanup timer)
- Green `●` marker in sessions list — visual confirmation that a session is safely in the XED library

### Changed
- Sessions sorted alphabetically descending by title (was: mtime) — newest numbered sessions like `XED03-...` appear first
- Reader preview and title resolution now prefer the archived copy over the live JSONL when both exist

### Fixed
- Flash messages (e.g. "Notiz aktuell") now clear immediately on any keypress instead of lingering

## [1.23.0] — 2026-03-10

### Added
- `install.sh` — one-command installer: `curl -fsSL https://tui.xed.dev/install.sh | bash`
- GitHub Pages at `https://tui.xed.dev` (CNAME + docs/)
- CI workflow: ruff linting + smoke test on Ubuntu/macOS × Python 3.11/3.13
- Multilingual landing pages: DE / FR / ES / PT / IT / HU / PL / BG / RO / RU / JA with language nav bar

### Changed
- PyPI: action-oriented description, expanded keywords (`anthropic`, `ai-coding`, `session-browser`, `jsonl`), sidebar URLs (`Documentation` wiki, `XED /Suite`)
- README: absolute URLs for PyPI rendering, screenshot placeholder with `raw.githubusercontent.com` URL
- README: full keybindings table, `xed.dev` and wiki links
- Branding: "XED /Suite" (`/`-prefix consistent across all pages)

### Fixed
- Renamed `xed-tui_v1.py` → `xed_tui_v1.py` (valid Python module name — removes `importlib.util` workaround)
- `termios`/`tty` conditional import for Windows compatibility (`print_paged` falls back to plain print)
- `.deb` shell wrapper shebang: replaced YAML heredoc with `printf` (leading whitespace bug)
- Removed npm from user-facing docs (workflow disabled)
- Version bump resolves PyPI version ordering: `1.23.0 > 1.22` (old scheme `v1.022` was PEP 440 `1.22`)

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
