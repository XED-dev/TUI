# AGENTS.md — XED /TUI
> Pflichtlektüre für alle AI-Agenten die in diesem Repo arbeiten.
> Englische Version: `../AGENTS.md` (AI-Übersetzung dieser Datei)
> Stand: April 2026

---

## PROJEKT

**XED /TUI** — mutt-artiger Session-Browser für Claude Code.
Terminal-first. Kein Cloud-Service. Kein proprietärer Lock-in.
Entwickelt von [Collective Context (CC)](https://collective-context.org) · Lizenz: MIT

**Zielgruppe:** Entwickler, Web-Agenturen und Freelancer im DACH-Raum —
und alle die Claude Code im Terminal nutzen.

---

## REGELN (nicht verhandelbar)

1. **JAIL:** Nur innerhalb dieses Repos schreiben — kein Zugriff auf andere Pfade.
2. **KEIN SUDO.** Niemals.
3. **NULL TERMINAL-COMMANDS OHNE EXPLIZITE FREIGABE.**
   Erlaubt ohne Freigabe: Read-Tool + Write-Tool. Sonst nichts.
3a. **KEINE DELETIONS DURCH AI-AGENTEN.** Absolut verboten sind
    `rm`, `rmdir`, `shred`, `unlink`, `find -delete`, `find -exec rm`,
    `shutil.rmtree`, `Path.unlink`, `fs.rm` und sprachliche Äquivalente.
    Nur der Human DevOps löscht. Wenn etwas weg muss: STOPP, Befehl
    vorschlagen, warten. Keine Ausnahmen — auch nicht für Build-Artefakte
    (`dist/`, `build/`, `__pycache__/`, `node_modules/`). Moderne Build-
    Werkzeuge (`uv build`, `pnpm build`, …) überschreiben idempotent.
4. **KEINE CREDENTIALS IM CODE.** Nur `os.environ[]`.
5. **WARTEN:** Nach jeder Frage auf Antwort warten. Nie vorausarbeiten.
6. **Bei Unsicherheit: STOPP. Fragen. Warten.**
7. **Issues immer referenzieren:** Jeder Fix-Commit muss eine Issue-Nummer enthalten.

---

## SPRACHPOLITIK

**Quelle:** `de/` — immer zuerst auf Deutsch schreiben.
**Release:** Root-Verzeichnis — AI übersetzt ins Englische.
**Regel:** Root-Dateien nie direkt bearbeiten.
           Immer zuerst `de/` aktualisieren, dann übersetzen.

**Übersetzungsbefehl:**
```
"Übersetze de/README.md ins Englische → README.md. Code-Blöcke unverändert lassen."
```

**Zukünftige Sprachen** (selbes Muster):
- `fr/` — Französisch (AI-Übersetzung aus EN oder DE)
- `ja/` — Japanisch
- `es/` — Spanisch

---

## WORKFLOW: Lab → Release

```
fb-data (privates Labor)          XED-dev/TUI (öffentlich)
──────────────────────────        ──────────────────────────
Tägliche Entwicklung         →    Milestone erreicht → Code-Sync
DE Docs schreiben in de/     →    AI übersetzt → root (EN)
                                  Community-Feedback via Issues
                                  Issues → postbox/todo.md
                                  → fließt zurück ins Labor
```

**Code-Sync:** Nur bei Milestones — kein täglicher Push.
**Docs-Sync:** Bei jedem Inhaltseintrag DE → EN übersetzen und zusammen committen.

---

## POSTBOX

```
postbox/todo.md    ← Community-Issues die ins Labor fließen
postbox/done.md    ← Audit-Log: Issue-Nr → Commit-Hash (Pflicht!)
postbox/cron.md    ← Geplante Milestones + Releases
postbox/attachments/  ← Komplexe Feature-Specs
```

**Kein Commit-Hash in done.md = Task gilt als nicht erledigt.**

---

## COMMIT-FORMAT

```
feat:     Neue Features
fix:      Bug-Fixes (#Issue-Nr)
docs:     Dokumentation (DE + EN immer zusammen)
release:  Neuer Release-Tag
chore:    Wartung
```

---

## ROLLEN

| Rolle | Wer | Aufgabe |
|---|---|---|
| **SysOps** | Maintainer | Freigaben, Priorisierung, Merge-Reviews |
| **Lab-Agent** | Claude Code (fb-data) | Entwicklung, Fixes |
| **Release-Agent** | Claude Code (xed/) | Übersetzung, Docs, Release-Commits |
| **Scanner** | Gemini CLI | Scannt Issues → schreibt in postbox/todo.md — löst NIE selbst |

---

*Standard: https://agents.md (Linux Foundation) · Projekt: https://collective-context.org*
