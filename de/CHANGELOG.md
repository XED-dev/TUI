# Changelog — XED /TUI
> Englische Version: [../CHANGELOG.md](../CHANGELOG.md)
> Format: [Keep a Changelog](https://keepachangelog.com/) · Versionierung: `MAJOR.MINOR`

---

## [1.25.0] — 2026-04-14

### Neu
- **Virtuelles `★ ARCHIV`-Projekt** ganz oben im Projekte-Panel — zeigt alle Notizen aus allen Projekten, auch verwaiste (Original-Session von Claude Code bereits gelöscht)
- **XED-Bibliothek unter `~/.xed/tui/archive/<proj>/<uuid>.jsonl`** — Schatten-Kopien der Claude-Code-Sessions, überleben Claudes Retention-Cleanup
- **Auto-Archivierung** bei `[e]` / `[E]` (Notiz bearbeiten) und `[u]` / `[U]` (Notiz aktualisieren) — jede Kuratierung sichert die Quell-Session
- **`[U]` Batch-Update** — alle Notizen im aktuellen Projekt in einem Rutsch aktualisieren/anlegen (N neu · N erneuert · N archiviert)
- **`[L]` Lend** — archivierte Session zurück ins `~/.claude/projects/<proj>/` kopieren, mtime frisch (resettet Claude Codes Cleanup-Zähler)
- Grüner `●`-Punkt in der Sessions-Liste — visuelle Bestätigung: diese Session liegt sicher in der XED-Bibliothek

### Geändert
- Sessions alphabetisch absteigend nach Titel sortiert (vorher: mtime) — neueste nummerierte Sessions wie `XED03-...` stehen oben
- Reader-Preview und Titel-Auflösung bevorzugen die archivierte Kopie gegenüber der Live-JSONL

### Behoben
- Flash-Nachrichten (z.B. „Notiz aktuell") verschwinden jetzt sofort beim nächsten Tastendruck statt zu überdauern

## [1.23.0] — 2026-03-10

### Neu
- `install.sh` — Ein-Befehl-Installer: `curl -fsSL https://tui.xed.dev/install.sh | bash`
- GitHub Pages unter `https://tui.xed.dev` (CNAME + docs/)
- CI-Workflow: ruff-Linting + Smoke-Test auf Ubuntu/macOS × Python 3.11/3.13
- Mehrsprachige Landing Pages: DE / FR / ES / PT / IT / HU / PL / BG / RO / RU / JA mit Sprachnavigation

### Geändert
- PyPI: aktionsorientierte Description, erweiterte Keywords (`anthropic`, `ai-coding`, `session-browser`, `jsonl`), Sidebar-URLs (`Documentation` Wiki, `XED /Suite`)
- README: absolute URLs für PyPI-Rendering, Screenshot-Platzhalter mit `raw.githubusercontent.com`-URL
- README: vollständige Tastenkürzel-Tabelle, `xed.dev`- und Wiki-Links
- Branding: „XED /Suite" (Slash-Präfix konsequent auf allen Seiten)

### Behoben
- `xed-tui_v1.py` → `xed_tui_v1.py` umbenannt (gültiger Python-Modulname — entfernt `importlib.util`-Workaround)
- `termios`/`tty` konditionaler Import für Windows-Kompatibilität (`print_paged` fällt auf einfaches print zurück)
- `.deb` Shell-Wrapper Shebang: YAML-Heredoc durch `printf` ersetzt (Leerzeichen-Bug)
- npm aus nutzersichtbaren Docs entfernt (Workflow deaktiviert)
- Versions-Bump behebt PyPI-Sortierung: `1.23.0 > 1.22` (altes Schema `v1.022` war PEP 440 `1.22`)

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
