# XED /TUI
> mutt-artiger Session-Browser für Claude Code — Terminal-first, kein Cloud-Service.
> Englische Version: `../README.md` (AI-Übersetzung dieser Datei)

**Organisation:** [Collective Context (CC)](https://collective-context.org) ·
**Lizenz:** MIT · **Version:** v1.018

---

## Was ist XED /TUI?

XED /TUI ist ein Terminal-Browser für Claude Code Sessions — inspiriert von mutt (E-Mail)
und ranger (Dateibrowser). Es läuft vollständig lokal, braucht keine API und keinen
Cloud-Service.

**Wer es braucht:** Jeder der Claude Code täglich nutzt und seine Sessions durchsuchen,
annotieren, fortsetzen oder verwalten möchte — direkt im Terminal.

---

## Installation

```bash
# Voraussetzungen: Python 3.8+ (nur stdlib, keine pip-Pakete nötig)
git clone https://github.com/XED-dev/TUI.git
cd TUI

# Starten
python src/xed-tui_v1.py
```

---

## Features — v1.018

- **4-Panel-Layout** — Projekte · Sessions · Reader · Notizen (Side-by-Side)
- **Session-Browser** — alle `~/.claude/projects/` sortiert nach Zeit
- **Reader** — vollständiger Transcript mit Markdown-Rendering
  (`**bold**`, `` `code` ``, `*italic*`, Tabellen, Code-Blöcke, Zitate)
- **`[a]` Resume** — Claude Code mit `--resume <uuid>` direkt starten (CWD automatisch)
- **`[r]` Clipboard** — `/resume <uuid>` → Zwischenablage (für laufendes Claude Code)
- **`[e]` Notizen** — pro Session eine `memory/<uuid>.md`, im `$EDITOR` bearbeitbar
- **`[t]` Titel** — Sessions umbenennen (erscheint in Claude Code + ZED History)
- **`[/]` Suche** — Live-Suche über alle Sessions
- **`Ctrl+R`** — Hot-Reload ohne Neustart

---

## Tastenkürzel

| Taste | Aktion |
|---|---|
| `↑↓` / `j k` | Navigation |
| `Tab` | Panel wechseln |
| `Enter` | Session öffnen |
| `a` | Claude Code --resume starten |
| `r` | Resume-CMD in Clipboard |
| `e` | Notiz im Editor öffnen |
| `t` | Titel setzen |
| `/` | Live-Suche |
| `f` | Reader-Vollbild |
| `n` | Notiz-Vollbild |
| `Ctrl+R` | Hot-Reload |
| `?` | Hilfe |
| `q` | Beenden |

→ Vollständige Referenz: [docs/de/keybindings.md](docs/de/keybindings.md)

---

## Warum XED /TUI?

ZED zeigt Claude Code Sessions im History-Panel — aber es gibt kein Tool um sie
**zu lesen, zu annotieren, zu durchsuchen und fortzusetzen** — bis XED /TUI.

Die Sessions liegen als `.jsonl` Dateien lokal — menschenlesbar, kein Lock-in.
XED /TUI ist der Browser dafür.

---

## Mitmachen

Alle Sprachen willkommen · All languages welcome.

→ [CONTRIBUTING.md](de/CONTRIBUTING.md) · [Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

---

*Building XED /TUI @ Collective Context (CC) · Lizenz: MIT*
