# XED /TUI

**Claude Code Sessions durchsuchen, lesen und fortsetzen — direkt im Terminal.**

> 🇬🇧 English version: [README.md](https://github.com/XED-dev/TUI/blob/main/README.md)

![XED /TUI — 4-Panel Session Browser](https://raw.githubusercontent.com/XED-dev/TUI/main/docs/images/hero.png)

## Installation

```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

Oder: `pipx install xed-tui` · `uv tool install xed-tui` · `brew install xed-dev/xed/xed-tui`

Voraussetzungen: [Claude Code](https://code.claude.com) installiert · Python 3.11+ · Linux, macOS oder WSL

## 30-Sekunden-Demo

```bash
xed-tui          # alle Sessions anzeigen
↑↓  Enter        # navigieren und lesen
/schema           # über alles suchen
a                 # in Claude Code fortsetzen
e                 # Notiz schreiben
?                 # Hilfe (DE/EN/FR/JA/ES)
```

## Warum XED /TUI?

| | XED /TUI | Alternativen |
|---|---|---|
| **Abhängigkeiten** | ✅ Keine (Python stdlib) | Go-Compiler / Node.js |
| **Notizen pro Session** | ✅ Smart Sync | Nicht verfügbar |
| **Markdown-Rendering** | ✅ Bold, Code, Tabellen | Rohtext |
| **Mehrsprachig** | ✅ 5 Sprachen | Nur Englisch |
| **Installationszeit** | ✅ ~5 Sekunden | Kompilieren nötig |

---

## Features

- **4-Panel-Layout** — Projekte · Sessions · Reader · Notizen
- **`a` Resume** — Claude Code mit `--resume <uuid>` starten (CWD automatisch)
- **`r` Clipboard** — `/resume <uuid>` in Zwischenablage für laufendes Claude Code
- **`e` Notizen** — pro Session eine Notiz mit Auto-Sync
- **`/` Suche** — Live-Volltext-Suche über Titel und Notizen
- **`#` Tags** — Sessions labeln, nach Tag filtern (`/#bugfix`)
- **`Ctrl+R`** — Hot-Reload, Stand bleibt erhalten
- **Mehrsprachige Hilfe** — DE / EN / FR / JA / ES

→ Vollständige Dokumentation: [Wiki](https://github.com/XED-dev/TUI/wiki) ·
[Quickstart](https://github.com/XED-dev/TUI/wiki/Installation) ·
[Tastenkürzel](https://github.com/XED-dev/TUI/wiki/Tastenkürzel)

→ Landing Page: [tui.xed.dev](https://tui.xed.dev) ·
XED /Suite: [xed.dev](https://xed.dev)

---

## Tastenkürzel

| Taste | Aktion |
|---|---|
| `↑↓` / `j k` | Navigieren |
| `Tab` / `← →` | Panel wechseln |
| `Enter` | Session öffnen |
| `a` | In Claude Code fortsetzen |
| `e` | Notiz bearbeiten |
| `/` | Suchen |
| `#` | Tags |
| `f` / `n` / `m` | Vollbild / Notizen / Swap |
| `?` | Hilfe (5 Sprachen) |
| `q` | Beenden |

→ [Alle Tastenkürzel](https://github.com/XED-dev/TUI/wiki/Tastenkürzel)

---

## Mitmachen

Alle Sprachen willkommen.
→ [CONTRIBUTING.md](https://github.com/XED-dev/TUI/blob/main/CONTRIBUTING.md) ·
[Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

*[Collective Context](https://collective-context.org) · MIT-Lizenz*
