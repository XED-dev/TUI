# Quickstart — XED /TUI
> Englische Version: `../../docs/quickstart.md`

## Voraussetzungen

- Python 3.8 oder neuer
- Claude Code installiert und eingerichtet
- Mindestens eine Claude Code Session vorhanden

## Installation

```bash
git clone https://github.com/XED-dev/TUI.git
cd TUI
python src/xed-tui_v1.py
```

Keine `pip install` nötig — nur Python-Stdlib (`curses`).

## Erster Start

Beim ersten Start liest XED /TUI automatisch `~/.claude/projects/` aus.
Du siehst deine Projekte links und die Sessions rechts davon.

```
┌─ Projekte ─┬─ Sessions ──────┬─ Reader ────────┬─ Notizen ─┐
│ fb-data    │ Session 1       │ [Inhalt]        │ [Notizen] │
│ github.io  │ Session 2       │                 │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
```

## Erste Schritte

1. `↑↓` — durch Sessions navigieren
2. `Enter` — Session öffnen und lesen
3. `a` — Session in Claude Code fortsetzen
4. `e` — Notiz zur Session schreiben
5. `?` — Alle Tastenkürzel anzeigen

## Nächste Schritte

→ [Tastenkürzel](keybindings.md) · [Architektur](architecture.md)
