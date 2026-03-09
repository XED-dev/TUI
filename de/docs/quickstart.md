# Quickstart — XED /TUI
> Englische Version: [../../docs/quickstart.md](../../docs/quickstart.md)

## Voraussetzungen

- Python 3.11 oder neuer
- Claude Code installiert und mindestens einmal gestartet (erstellt `~/.claude/projects/`)
- Unix-Terminal: Linux, macOS oder WSL

## Installation

### Empfohlen — uv
```bash
uv tool install xed-tui
```

### pip / pipx
```bash
pipx install xed-tui
```

### npm (für Claude Code Nutzer)
```bash
npm install -g @xed-dev/tui
```

Keine weitere `pip install` nötig — nur Python-Stdlib (`curses`).

## Erster Start

```bash
xed-tui
```

Beim ersten Start liest XED /TUI automatisch `~/.claude/projects/` aus.
Projekte links, Sessions rechts davon.

```
┌─ Projekte ─┬─ Sessions ──────┬─ Reader ────────┬─ Notizen ─┐
│ fb-data  3 │ #1  Mo  Mein ... │ ▶ YOU           │ [Notizen] │
│ github   1 │ #2  Fr  Bug  ... │ Frage hier      │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
 [?/H]Hlp [/]Find [#]Tag [T]Tit [D]Del [A]Agt [^E]Set ...
```

## Erste Schritte

1. `↑↓` — durch Sessions navigieren
2. `Enter` — Session öffnen und lesen
3. `a` — Session in Claude Code fortsetzen
4. `e` — Notiz zur Session schreiben
5. `Ctrl+E` — Editor und Standard-App konfigurieren
6. `?` — Alle Tastenkürzel anzeigen (5 Sprachen)

## Letzten Stand wiederherstellen

```bash
xed-tui --continue
```

Der Stand wird automatisch beim Beenden und Hot-Reload (`Ctrl+R`) gespeichert.

## Nächste Schritte

→ [Tastenkürzel](keybindings.md) · [Architektur](architecture.md)
