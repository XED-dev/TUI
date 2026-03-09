#!/usr/bin/env node
"use strict";

const { execFileSync, spawnSync } = require("child_process");
const path = require("path");

function findPython() {
  for (const py of ["python3", "python"]) {
    try {
      const out = execFileSync(py, ["--version"], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      });
      const m = (out + "").match(/Python (\d+)\.(\d+)/);
      if (m && (parseInt(m[1]) > 3 || (parseInt(m[1]) === 3 && parseInt(m[2]) >= 11))) {
        return py;
      }
    } catch (_) {}
  }
  return null;
}

const python = findPython();
if (!python) {
  console.error(
    "\n  xed-tui requires Python 3.11+\n" +
    "  Install: https://python.org/downloads\n" +
    "  Or via uv: https://docs.astral.sh/uv/\n"
  );
  process.exit(1);
}

// Run the bundled script directly — no pip install required
const script = path.join(__dirname, "..", "lib", "xed_tui_v1.py");
const result = spawnSync(python, [script, ...process.argv.slice(2)], {
  stdio: "inherit",
});
process.exit(result.status ?? 1);
