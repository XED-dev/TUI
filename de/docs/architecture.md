# Architektur — XED /TUI
> Englische Version: `../../docs/architecture.md`

## Überblick

XED /TUI ist in reinem Python geschrieben — ausschließlich stdlib, keine Abhängigkeiten.

```
src/xed_tui/xed-tui_v1.py   (~2400 Zeilen)
├── State-Layer      — Sessions, Projekte, Continue-State lesen/schreiben
├── Parser-Layer     — JSONL parsen, Markdown inline rendern
├── Layout-Layer     — 4 curses-Panels verwalten
└── Key-Dispatch     — Tastatureingaben → Aktionen
```

## Datenquellen

```
~/.claude/projects/<slug>/
├── <uuid>.jsonl          ← Session-Transcript (eine Zeile = ein JSON-Objekt)
├── memory/
│   ├── MEMORY.md         ← Persistentes Gedächtnis (auto-geladen von Claude Code)
│   ├── titles.json       ← Custom-Titel (von XED /TUI geschrieben)
│   └── <uuid>.md         ← Session-Notizen
└── ~/.local/share/xed-tui/continue.json  ← UI-Zustand für Hot-Reload
```

## v1 vs. v2 (Roadmap)

| Komponente | v1 (curses) | v2 (urwid, geplant) |
|---|---|---|
| Layout | `curses.newwin()`, manuell | `urwid.Columns` / `urwid.Pile` |
| Maus | ❌ | `mouse_event()` nativ |
| Rendering | alles neu bei Änderung | nur Diffs (Canvas-Diff) |
| Key-Dispatch | if-elif-Kette | Dispatch-Tabelle |
| Async | ❌ | `urwid.AsyncioEventLoop` |

## Entwicklungsworkflow

Tägliche Entwicklung: `fb-data/scripts/bin/XED-TUI/xed-tui_v1.py`
Release-Sync: → `xed/src/xed_tui/xed-tui_v1.py` bei Milestones
