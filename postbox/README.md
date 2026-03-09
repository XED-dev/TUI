# Postbox — XED /TUI
> Async-Koordination zwischen Community und Lab · [CC Best Practice](https://collective-context.org/cc/postbox-pattern)

---

## Workflow

```
GitHub Issue          →  postbox/todo.md  →  fb-data Labor  →  Fix  →  done.md + Release
Community-Wunsch         (triage hier)       (Entwicklung)       ↑
                                                                  |
                                                          Commit-Hash Pflicht
```

---

## Dateien

| Datei | Zweck |
|---|---|
| `todo.md` | Offene Issues die ins Labor fließen |
| `done.md` | Audit-Log: Issue-Nr → fb-data Commit-Hash |
| `cron.md` | Geplante Milestones + Release-Termine |
| `attachments/todo/` | Komplexe Feature-Specs |
| `attachments/cron/` | Release-Arbeitsanweisungen |
| `attachments/done/` | Archiv — nie löschen |

## Regeln

- **Kein Commit-Hash in done.md = Task gilt als nicht erledigt.**
- `attachments/done/` wird nie gelöscht — vollständiger Audit-Trail.
- Milestones in `cron.md` erscheinen 30 Tage vor Termin in `todo.md`.

---

*[CC Postbox Pattern](https://collective-context.org/cc/postbox-pattern)*
