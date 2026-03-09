# Changelog — XED /TUI
> Englische Version: [../CHANGELOG.md](../CHANGELOG.md)
> Format: [Keep a Changelog](https://keepachangelog.com/) · Versionierung: `MAJOR.MINOR`

---

## [1.0.23] — unveröffentlicht

### Geändert
- Versionierung auf 3-stelliges Semver umgestellt (`MAJOR.MINOR.PATCH`) — bisheriges `1.022` wurde von PyPI zu `1.22` normalisiert (PEP 440), was zu Abweichungen in Homebrew und Install-Befehlen führte

## [1.22] — 2026-03-09
*Vorher als `v1.022` getaggt — PyPI hat die Version normalisiert.*

### Neu
- `Ctrl+E` — Einstellungen-Overlay: Editor (`auto` / `msedit` / `nano` / custom) und Standard-App (`auto` / `typora` / custom) konfigurieren
- `[E]` respektiert `editor_pref`-Einstellung; `[O]` respektiert `open_pref`-Einstellung
- Einstellungen in `continue.json` gespeichert — bleiben über Sessions und Hot-Reloads erhalten
- Hilfetexte in allen 5 Sprachen aktualisiert (DE / EN / FR / JA / ES)
- Statuszeile: `[^E]Set` Hinweis

## [1.021] — 2026-03-07

### Neu
- Mehrsprachiges Hilfe-Overlay (DE / EN / FR / JA / ES), umschaltbar mit `←→` oder Zahlentasten `1–5`
- Sprachpräferenz in `continue.json` gespeichert

## [1.020] — 2026-03-06

### Neu
- `[#]` Tags: Labels pro Session, gespeichert in `memory/tags.json`
- Tag-Filter: `/#tag` im Such-Modus filtert Sessions nach Tag
- Token-Zähler: `output_tokens` als `42k` im Sessions-Panel angezeigt

## [1.018] — 2026-03-05

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
- ~2400 Zeilen reines Python · nur `curses` (stdlib) · keine Abhängigkeiten
- `CONTINUE_STATE_PATH`: `~/.local/share/xed-tui/continue.json`

---

*Ältere Entwicklungshistorie: [fb-data](https://github.com/edikte/fb-data/commits/main/scripts/bin/XED-TUI/)*
