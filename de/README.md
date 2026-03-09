# XED /TUI
> mutt-artiger Session-Browser für Claude Code — Terminal-first, kein Cloud-Service.
> Englische Version: [../README.md](../README.md)

**Organisation:** [Collective Context (CC)](https://collective-context.org) ·
**Lizenz:** MIT · **Version:** v1.022

---

## Was ist XED /TUI?

XED /TUI ist ein Terminal-Browser für Claude Code Sessions — inspiriert von mutt (E-Mail)
und ranger (Dateibrowser). Es läuft vollständig lokal, braucht keine API und keinen
Cloud-Service.

**Wer es braucht:** Jeder der Claude Code täglich nutzt und seine Sessions durchsuchen,
annotieren, fortsetzen oder verwalten möchte — direkt im Terminal.

---

## Installation

### Empfohlen — uv (schnellste Methode)
```bash
uv tool install xed-tui
```

### pip / pipx
```bash
pipx install xed-tui
# oder:
pip install xed-tui
```

### npm
```bash
npm install -g @xed-dev/tui
```

### Aus dem Quellcode
```bash
git clone https://github.com/XED-dev/TUI.git
cd TUI
python -m xed_tui
```

**Voraussetzungen:** Python 3.11+ · Unix-Terminal (Linux, macOS, WSL) · keine pip-Pakete nötig

---

## Features — v1.022

- **4-Panel-Layout** — Projekte · Sessions · Reader · Notizen (Side-by-Side)
- **Session-Browser** — alle `~/.claude/projects/` sortiert nach Aktualität
- **Reader** — vollständiger Transcript mit Markdown-Rendering (`**bold**`, `` `code` ``, Tabellen, Code-Blöcke)
- **`[a]` Resume** — Claude Code mit `--resume <uuid>` starten (CWD automatisch)
- **`[r]` Clipboard** — `/resume <uuid>` → Zwischenablage (für laufendes Claude Code)
- **`[e]` Notizen** — pro Session eine `memory/<uuid>.md`, im Editor bearbeitbar
- **`[o]` Öffnen** — Notiz in Standard-App öffnen (z.B. Typora, Obsidian)
- **`[t]` Titel** — Sessions umbenennen (synct mit Claude Code + ZED History)
- **`[/]` Suche** — Live-Suche über Titel und Notizen
- **`[#]` Tags** — Sessions labeln, nach Tag filtern (`/#hvd`)
- **`Ctrl+E`** — Einstellungen: Editor und Standard-App konfigurieren
- **`Ctrl+R`** — Hot-Reload, Stand bleibt via `--continue` erhalten
- **Mehrsprachige Hilfe** — DE / EN / FR / JA / ES (`?`-Taste)

---

## Schnellstart

```bash
xed-tui                  # starten
xed-tui --continue       # letzten Stand wiederherstellen
xed-tui --help           # vollständige Tastenkürzel-Referenz
```

→ Vollständige Anleitung: [docs/quickstart.md](docs/quickstart.md)

---

## Tastenkürzel

| Taste | Aktion |
|-------|--------|
| `↑↓` / `j k` | Navigation |
| `Tab` / `← →` | Panel wechseln |
| `Enter` | Session öffnen |
| `a` | Claude Code --resume starten |
| `r` | Resume-CMD in Clipboard |
| `e` | Notiz im Editor öffnen |
| `o` | Notiz in Standard-App öffnen |
| `t` | Titel setzen |
| `/` | Live-Suche |
| `#` | Tags setzen |
| `f` | Reader-Vollbild |
| `n` | Notiz-Vollbild |
| `Ctrl+E` | Einstellungen (Editor, App) |
| `Ctrl+R` | Hot-Reload |
| `?` | Hilfe (5 Sprachen) |
| `q` | Beenden |

→ Vollständige Referenz: [docs/keybindings.md](docs/keybindings.md)

---

## Warum XED /TUI?

ZED und Claude Code haben kein eingebautes Tool um Sessions **zu lesen, zu annotieren,
zu durchsuchen und fortzusetzen**. Sessions liegen als `.jsonl` Dateien lokal —
menschenlesbar, kein Lock-in. XED /TUI ist der Browser dafür.

---

## Mitmachen

Alle Sprachen willkommen · All languages welcome.

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Issues](https://github.com/XED-dev/TUI/issues) ·
[Discussions](https://github.com/XED-dev/TUI/discussions)

---

*Building XED /TUI @ Collective Context (CC) · Lizenz: MIT*
