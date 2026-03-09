# Quickstart — XED /TUI
> Englische Version: [../../docs/quickstart.md](../../docs/quickstart.md)

## Schritt 1 — Claude Code installieren

XED /TUI ist ein Session-Browser für Claude Code. Es liest die Session-Dateien,
die Claude Code in `~/.claude/projects/` ablegt. Claude Code muss installiert
und mindestens einmal gestartet worden sein, bevor XED /TUI genutzt werden kann.

**Linux / macOS:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows — empfohlen: WSL:**
```powershell
wsl --install            # falls WSL noch nicht eingerichtet
# dann innerhalb WSL:
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows — Alternative: nativ (winget):**
```powershell
winget install Anthropic.ClaudeCode
```

Dann Claude Code einmal starten, damit das Session-Verzeichnis angelegt wird:
```bash
claude
```

→ Claude Code Dokumentation: [code.claude.com](https://code.claude.com)

## Schritt 2 — XED /TUI installieren

Ein Befehl — gleiche Methode wie bei Claude Code:

```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

Das installiert `xed-tui` nach `~/.local/bin/` — direkt neben `claude`.

**Alternative Methoden:**
```bash
pipx install xed-tui       # wenn du pipx verwendest
uv tool install xed-tui    # wenn du uv verwendest
brew install xed-tui       # macOS / Linux (Homebrew)
pip install --user xed-tui # einfaches pip
```

**Windows-User:** Den Install-Befehl innerhalb von WSL oder Git Bash ausführen —
demselben Terminal, in dem Claude Code läuft.

## Schritt 3 — Starten

```bash
xed-tui
```

XED /TUI liest die Claude Code Sessions automatisch aus:

```
┌─ Projekte ─┬─ Sessions ──────┬─ Reader ────────┬─ Notizen ─┐
│ fb-data  3 │ #1  Mo  Mein ... │ ▶ YOU           │ [Notizen] │
│ github   1 │ #2  Fr  Bug  ... │ Frage hier      │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
 [?/H]Hlp [/]Find [#]Tag [T]Tit [D]Del [A]Agt [^E]Set ...
```

1. `↑↓` — durch Sessions navigieren
2. `Enter` — Session öffnen und lesen
3. `a` — Session in Claude Code fortsetzen
4. `e` — Notiz schreiben
5. `?` — Hilfe (DE / EN / FR / JA / ES)

## Letzten Stand wiederherstellen

```bash
xed-tui --continue
```

Der Stand wird automatisch beim Beenden und Hot-Reload (`Ctrl+R`) gespeichert.

## Nächste Schritte

→ [Tastenkürzel](keybindings.md) · [Architektur](architecture.md)
