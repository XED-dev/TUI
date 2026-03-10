# XED /TUI

**Claude Code Sessions durchsuchen, lesen und fortsetzen — direkt im Terminal.**

> 🇬🇧 English version: [../README.md](../README.md)

<!--
  Screenshot-Platzhalter — nach Aufnahme einfügen:
  ![XED /TUI — 4-Panel Session Browser](../docs/images/hero.png)
-->

Claude Code speichert jedes Gespräch als lokale Datei. XED /TUI macht sie
zugänglich: alle Sessions durchsuchen, vollständige Transcripts mit
Markdown-Rendering lesen, Notizen schreiben und mit einem Tastendruck zu
jeder Session zurückspringen.

## Installation

```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

Voraussetzungen: Claude Code · Python 3.11+ · Linux, macOS oder WSL

**Alternative Methoden:**
```bash
pipx install xed-tui
uv tool install xed-tui
brew install xed-dev/xed/xed-tui
```

## 30-Sekunden-Demo

```bash
xed-tui          # starten
```

| Taste | Aktion |
|-------|--------|
| `↑↓` | Sessions durchblättern |
| `Enter` | Vollständigen Transcript lesen |
| `/` | Über alle Sessions suchen |
| `a` | Session in Claude Code fortsetzen |
| `e` | Notiz schreiben |
| `?` | Hilfe (DE / EN / FR / JA / ES) |

→ Vollständige Referenz: [docs/keybindings.md](../docs/keybindings.md)

## Warum XED /TUI?

| Feature | XED /TUI | claude-dashboard | claude-session-browser |
|---------|----------|-----------------|----------------------|
| Keine Abhängigkeiten | ✅ nur Python stdlib | ❌ Go-Binary | ❌ Go-Binary |
| Notizen pro Session | ✅ Smart Sync | ❌ | ❌ |
| Volltext-Suche | ✅ Live-Filter | ✅ | ✅ |
| Markdown-Rendering | ✅ bold, code, Tabellen | ❌ Rohtext | ❌ Rohtext |
| Mehrsprachige Hilfe | ✅ DE/EN/FR/JA/ES | ❌ | ❌ |
| Resume per Tastendruck | ✅ `a` → `--resume` | ✅ | ✅ |
| Installationszeit | ~5 Sek. (pip) | Go nötig | Go nötig |

## Features

- **4-Panel-Layout** — Projekte · Sessions · Reader · Notizen (Side-by-Side)
- **`a` Resume** — Claude Code mit `--resume <uuid>` starten (CWD automatisch)
- **`r` Clipboard** — `/resume <uuid>` in Zwischenablage für laufendes Claude Code
- **`e` Notizen** — pro Session eine `memory/<uuid>.md`, im Editor bearbeitbar
- **`/` Suche** — Live-Suche über Titel und Notizen
- **`#` Tags** — Sessions labeln, nach Tag filtern (`/#bugfix`)
- **`Ctrl+R`** — Hot-Reload, Stand bleibt via `--continue` erhalten

→ Vollständige Anleitung: [Wiki](https://github.com/XED-dev/TUI/wiki) ·
[Quickstart](../docs/quickstart.md) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

## Mitmachen

Alle Sprachen willkommen · All languages welcome.

→ [CONTRIBUTING.md](../CONTRIBUTING.md) · [Issues](https://github.com/XED-dev/TUI/issues)

---

**Version:** v1.0.24 · **Lizenz:** MIT · **Org:** [Collective Context](https://collective-context.org) · **PyPI:** [xed-tui](https://pypi.org/project/xed-tui/)
