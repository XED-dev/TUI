# AGENTS.md — XED /TUI
> Required reading for all AI agents working in this repository.
> German source: `de/AGENTS.md` — this file is an AI translation.
> Last updated: March 2026

---

## PROJECT

**XED /TUI** — a mutt-style session browser for Claude Code.
Terminal-first. No cloud service. No proprietary lock-in.
Built by [Collective Context (CC)](https://collective-context.org) · License: MIT

**Primary audience:** Developers, web agencies and freelancers in the DACH region —
and everyone using Claude Code in the terminal.

---

## RULES (non-negotiable)

1. **JAIL:** Write only within this repository — no access to other paths.
2. **NO SUDO.** Ever.
3. **NO TERMINAL COMMANDS WITHOUT EXPLICIT APPROVAL.**
   Allowed without approval: Read tool + Write tool. Nothing else.
4. **NO CREDENTIALS IN CODE.** Use `os.environ[]` only.
5. **WAIT:** After every question, wait for a response. Never work ahead.
6. **When in doubt: STOP. Ask. Wait.**
7. **Always reference issues:** Every fix commit must include an issue number.

---

## LANGUAGE POLICY

**Source:** `de/` — always written first, in German.
**Release:** Root directory — AI-translated to English.
**Rule:** Never edit root-level docs directly.
           Always update `de/` first, then translate.

**Translation command:**
```
"Translate de/README.md to English → README.md. Keep code blocks unchanged."
```

**Future languages** (same pattern):
- `fr/` — French (AI translation from EN or DE)
- `ja/` — Japanese
- `es/` — Spanish

---

## WORKFLOW: Lab → Release

```
fb-data (private lab)             XED-dev/TUI (public)
──────────────────────────        ──────────────────────────
Daily development            →    Milestone reached → code sync
Write DE docs in de/         →    AI translates → root (EN)
                                  Community feedback via Issues
                                  Issues → postbox/todo.md
                                  → flows back into the lab
```

**Code sync:** Only at milestones — no daily pushes.
**Docs sync:** With every content update, translate DE → EN and commit both together.

---

## POSTBOX

```
postbox/todo.md       ← Community issues flowing into the lab
postbox/done.md       ← Audit log: issue number → commit hash (required!)
postbox/cron.md       ← Planned milestones + releases
postbox/attachments/  ← Complex feature specs
```

**No commit hash in done.md = task is not considered done.**

---

## COMMIT FORMAT

```
feat:     New features
fix:      Bug fixes (#issue-number)
docs:     Documentation (DE + EN always committed together)
release:  New release tag
chore:    Maintenance
```

---

## ROLES

| Role | Who | Responsibility |
|---|---|---|
| **SysOps** | Maintainer | Approvals, prioritization, merge reviews |
| **Lab Agent** | Claude Code (fb-data) | Development, fixes |
| **Release Agent** | Claude Code (xed/) | Translation, docs, release commits |
| **Scanner** | Gemini CLI | Scans issues → writes to postbox/todo.md — NEVER fixes |

---

*Standard: https://agents.md (Linux Foundation) · Project: https://collective-context.org*
