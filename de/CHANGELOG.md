# Changelog — XED /TUI
> Englische Version: `../CHANGELOG.md` (AI-Übersetzung dieser Datei)
> Format: [Keep a Changelog](https://keepachangelog.com/) · [Semantic Versioning](https://semver.org/)

---

## [v1.018] — 2026-03-09

### Erstes öffentliches Release

**Neu:**
- 4-Panel-Layout: Projekte · Sessions · Reader · Notizen
- Vollständiges Markdown-Rendering (bold, italic, code, Tabellen mit Box-Drawing)
- `[a]` Claude Code `--resume` direkt aus der TUI starten
- `[r]` `/resume <uuid>` in Zwischenablage kopieren
- `[e]` Session-Notizen im `$EDITOR` bearbeiten
- `[t]` Sessions umbenennen (native JSONL, kompatibel mit ZED History)
- `[/]` Live-Suche über alle Sessions
- `Ctrl+R` Hot-Reload (Stand bleibt erhalten via `--continue`)
- Startup-Preview: letzter Zustand wird beim Start wiederhergestellt

**Behoben:**
- v1.016: `draw_table_row()` schrieb hardcoded ASCII `|` statt Unicode `│`
- v1.017: Spaltenbreiten in Tabellen basierten auf Markdown-Länge statt visueller Länge
- v1.018: Leeres Vorschau-Panel beim Start wenn `focus != "threads"`

**Technisch:**
- ~1800 Zeilen reines Python · nur `curses` (stdlib) · keine Abhängigkeiten
- `CONTINUE_STATE_PATH`: `~/.local/share/xed-tui/continue.json`

---

*Ältere Entwicklungshistorie: [fb-data](https://github.com/edikte/fb-data/commits/main/scripts/bin/XED-TUI/)*
