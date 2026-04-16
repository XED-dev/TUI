# Changelog — XED /TUI
> Englische Version: [../CHANGELOG.md](../CHANGELOG.md)
> Format: [Keep a Changelog](https://keepachangelog.com/) · Versionierung: `MAJOR.MINOR`

---

## [1.26.4] — 2026-04-16

### Behoben
- **`xed-tui claude <title>` übergibt jetzt den Titel an `claude --resume`, nicht die UUID.** Claude Code v2.x behandelt das `--resume`-Argument als custom-title / session_name — UUID-Resume scheitert bei Sessions mit mehreren `custom-title`-Records (die jede Session nach einem `[U]`-Lauf mit v1.26.1's `repair_custom_title_format` hat). Fehler war `No conversation found with session ID: <uuid>`. v1.26.4 übergibt den vollen Titel-String, den XED bereits aufgelöst hat — Claude verarbeitet das sauber. Bonus: Tippt man `claude --resume "AG006"` direkt (kurzer Prefix, nicht eindeutig), öffnet Claude v2.x den interaktiven Resume-Picker vorgefiltert — angenehmer Fallback bei Unschärfe.

## [1.26.3] — 2026-04-15

### Neu
- **`xed-tui claude <title-pattern>` CLI-Subcommand** — findet eine Live-Session per Titel (case-insensitive Substring) über alle Projekte hinweg und ersetzt den Python-Prozess durch `claude --resume <uuid>` im richtigen `cwd`. Titel-Auflösung folgt der TUI-Priorität (nativer `custom-title` in JSONL → `titles.json` → erste User-Message). Bei mehreren Treffern: Liste auf stderr, exit 2. Bei null Treffern: exit 1 mit Hinweis auf `[L]` Lend für nur-archivierte Sessions.
- Konvention: Bei unserem Workflow beginnt der Titel immer mit `"AA000"` bis `"ZZ999"` (5 Zeichen: 2 Buchstaben + 3 Ziffern, z.B. `AG006`, `AI022`). Dieses 5-Zeichen-Präfix reicht meist als eindeutige Session-ID — `xed-tui claude AG006` nimmt die Session auf, keine UUID mehr tippen.

## [1.26.2] — 2026-04-15

### Behoben
- **Titel nach XED-Neustart veraltet, wenn die Session eine ältere Archivkopie hat.** `title()` las den nativen `custom-title` über `resolved_jsonl()` — das ist archiv-bevorzugt. Wenn XED eine Session _nach_ dem letzten Archiv-Snapshot umbenannt hatte, behielt das Archiv den alten `custom-title`; beim nächsten XED-Start gewann das Archiv wieder und der alte Titel erschien sowohl in der normalen Projekt-Liste als auch in `★ ARCHIV`. v1.26.2 liest den nativen Titel aus der **Live**-JSONL, wann immer sie existiert (Source-of-Truth für aktuelle Renames), und fällt nur bei verwaisten Sessions auf das Archiv zurück. Content-Reader-Pfade (`first_human_title`, `_build_reader_lines`) bleiben archiv-bevorzugt (Cleanup-Resilienz nach Claudes 90-Tage-Lifecycle).

## [1.26.1] — 2026-04-15

### Behoben
- **`custom-title`-Records werden jetzt im kompakten Claude-nativen Format geschrieben.** XED benutzte bisher Pythons Default-`json.dumps`, das Whitespace-Padding setzt (`{"type": "custom-title", …}`). Die History-/Resume-UIs von Claude Code und ZED parsen Session-Labels mit whitespace-sensitiven Patterns und haben XED-Records stillschweigend ignoriert — von XED umbenannte Sessions erschienen in diesen UIs unter der ersten User-Message statt unter dem neuen Titel. v1.26.1 schreibt mit `separators=(",", ":")` (`{"type":"custom-title",…}`), bit-identisch zu dem was Claude selbst schreibt.
- **`[U]` Batch-Update repariert pre-v1.26.1-Sessions rückwirkend.** `repair_custom_title_format()` hängt einen kompakten Rewrite des zuletzt gesetzten Titels an jede JSONL an, deren letzter `custom-title`-Record noch whitespace-gepaddet ist. Idempotent, append-only, nicht-destruktiv — läuft automatisch bei `[U]` und meldet `N Titel repariert` im Status. Sessions, die nie per `[U]` berührt werden, bleiben wie sie sind; ein einmaliges `[T]` Rename produziert ebenfalls das neue Format.

## [1.26.0] — 2026-04-15

### Neu
- **Notiz-Mitarchivierung (M0)** — bei `[e]` / `[E]` / `[u]` / `[U]` wird die Per-Session-Notiz `<uuid>.md` jetzt parallel zur JSONL nach `~/.xed/tui/archive/<proj>/<uuid>.md` kopiert. Die Notiz ist die kuratierte Katalogkarte — sie überlebt nun zusammen mit dem Band.
- **`[L]` Lend bringt die Notiz mit** — liegt eine archivierte `<uuid>.md` vor, wird sie ebenfalls nach `memory/<uuid>.md` zurückgespielt. Statusmeldung zeigt `Ausgeliehen + Notiz:` wenn beides zurückkam.
- **Stats-Zeile im `★ ARCHIV`** — einzeilige Zusammenfassung oben im Sessions-Panel: Bände · Katalogkarten · Gesamtgröße · Datumsspanne · Top-Projekt. Keine Datenbank, nur `os.stat()` — skaliert locker in den Tausender-Bereich.
- **Ranking-Suche mit Kontext-Snippets** — `/` gewichtet jetzt (Titel-Treffer 10×, Notiz-Treffer 1×) und sortiert nach Relevanz. Bei einem Notiz-Treffer, der nicht im Titel steckt, erscheint ein kurzes `«…Snippet…»` in der Sessions-Zeile.

### Geändert
- **Sidecar-Migration (M1–M4)** — XED-eigene Sidecars ziehen aus `~/.claude/projects/<proj>/memory/` nach `~/.xed/tui/state/`:
  - `continue.json` → `~/.xed/tui/state/continue.json` (vorher `~/.local/share/xed-tui/`)
  - `titles.json` / `tags.json` → `~/.xed/tui/state/<proj>/`
  - `<uuid>.sync` → `~/.xed/tui/state/<proj>/<uuid>.sync`
  - Per-Session-Notiz `<uuid>.md` **bleibt** im `memory/` — sie ist die Brücke zu Claudes Auto-Memory.
  - Externe Tools (Claude Code, ZED) sind nicht betroffen: die Titel-Quelle ist der `custom-title`-Record in der JSONL selbst, nicht `titles.json`.
- **Lazy-Migration** — Reader fallen auf die alten Pfade zurück, wenn der neue Ort leer ist. Upgrades bleiben unterbruchsfrei. Writes gehen immer in die neue Heimat.

### Docs
- README bekommt einen **Backup**-Abschnitt mit Verweis auf Syncthing / rsync / git-annex — XED /TUI liefert absichtlich keine eigene Sync-Lösung.

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
