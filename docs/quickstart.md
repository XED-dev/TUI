# Quickstart — XED /TUI
> German version: [../de/docs/quickstart.md](../de/docs/quickstart.md)

## Step 1 — Install Claude Code

XED /TUI is a session browser for Claude Code. It reads the session files
that Claude Code creates in `~/.claude/projects/`. Claude Code must be
installed and started at least once before XED /TUI can be used.

**Linux / macOS:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows — recommended: WSL:**
```powershell
wsl --install            # if WSL not yet set up
# then inside WSL:
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows — alternative: native (winget):**
```powershell
winget install Anthropic.ClaudeCode
```

Then start Claude Code once to create the session directory:
```bash
claude
```

→ Full Claude Code docs: [code.claude.com](https://code.claude.com)

## Step 2 — Install XED /TUI

One command — same pattern as Claude Code:

```bash
curl -fsSL https://tui.xed.dev/install.sh | bash
```

This installs `xed-tui` into `~/.local/bin/` — right next to `claude`.

**Alternative methods:**
```bash
pipx install xed-tui       # if you use pipx
uv tool install xed-tui    # if you use uv
brew install xed-tui       # macOS / Linux (Homebrew)
pip install --user xed-tui # plain pip
```

**Windows users:** Run the install command inside WSL or Git Bash —
the same terminal where Claude Code runs.

## Step 3 — Start

```bash
xed-tui
```

XED /TUI reads your Claude Code sessions automatically:

```
┌─ Projects ─┬─ Sessions ──────┬─ Reader ────────┬─ Notes ───┐
│ fb-data  3 │ #1  Mon  My ...  │ ▶ YOU           │ [notes]   │
│ github   1 │ #2  Fri  Bug ... │ question here   │           │
└────────────┴─────────────────┴─────────────────┴───────────┘
 [?/H]Hlp [/]Find [#]Tag [T]Tit [D]Del [A]Agt [^E]Set ...
```

1. `↑↓` — navigate sessions
2. `Enter` — read a session
3. `a` — resume session in Claude Code
4. `e` — write a note
5. `?` — help (DE / EN / FR / JA / ES)

## Restore last state

```bash
xed-tui --continue
```

State is saved automatically on quit and hot-reload (`Ctrl+R`).

## Next steps

→ [Keybindings](keybindings.md) · [Architecture](architecture.md)
