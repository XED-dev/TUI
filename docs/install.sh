#!/bin/sh
# XED /TUI Installer — mirrors Claude Code's installation pattern
# Usage: curl -fsSL https://tui.xed.dev/install.sh | bash
set -e

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
RED="\033[31m"
RESET="\033[0m"

info()  { printf "${CYAN}${BOLD}→${RESET} %s\n" "$1"; }
ok()    { printf "${GREEN}${BOLD}✓${RESET} %s\n" "$1"; }
fail()  { printf "${RED}${BOLD}✗${RESET} %s\n" "$1"; exit 1; }

# ── Step 1: Check Python ────────────────────────────────────────────────────

PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)
    if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  fail "Python 3.11+ required but not found.
    Linux:   sudo apt install python3  (or dnf / pacman)
    macOS:   brew install python@3.13
    WSL:     sudo apt install python3"
fi

ok "Python found: $PYTHON ($version)"

# ── Step 2: Check Claude Code ───────────────────────────────────────────────

if [ ! -d "$HOME/.claude" ]; then
  info "Claude Code not detected (~/.claude not found)"
  info "XED /TUI reads Claude Code sessions — install Claude Code first:"
  printf "\n    curl -fsSL https://claude.ai/install.sh | bash\n\n"
  info "Then run this installer again."
  exit 1
fi

ok "Claude Code detected"

# ── Step 3: Install via pipx / uv / pip ────────────────────────────────────

if command -v pipx >/dev/null 2>&1; then
  info "Installing via pipx..."
  pipx install xed-tui --force
elif command -v uv >/dev/null 2>&1; then
  info "Installing via uv..."
  uv tool install xed-tui --force
else
  info "Installing via pip..."
  "$PYTHON" -m pip install --user --upgrade xed-tui
fi

# ── Step 4: Verify PATH ─────────────────────────────────────────────────────

if command -v xed-tui >/dev/null 2>&1; then
  ok "xed-tui installed successfully"
  printf "\n  ${BOLD}Start with:${RESET}  xed-tui\n\n"
else
  LOCAL_BIN="$HOME/.local/bin"
  if [ -f "$LOCAL_BIN/xed-tui" ] && ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    info "Adding $LOCAL_BIN to PATH..."
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
      if [ -f "$rc" ]; then
        echo "export PATH=\"$LOCAL_BIN:\$PATH\"" >> "$rc"
      fi
    done
    ok "xed-tui installed — restart your shell or run:"
    printf "\n  export PATH=\"%s:\$PATH\"\n  xed-tui\n\n" "$LOCAL_BIN"
  else
    fail "Installation succeeded but xed-tui not found in PATH."
  fi
fi
