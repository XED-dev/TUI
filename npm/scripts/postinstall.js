"use strict";

const { execFileSync } = require("child_process");

function check() {
  for (const py of ["python3", "python"]) {
    try {
      const out = execFileSync(py, ["--version"], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      });
      const m = (out + "").match(/Python (\d+)\.(\d+)/);
      if (m && (parseInt(m[1]) > 3 || (parseInt(m[1]) === 3 && parseInt(m[2]) >= 11))) {
        console.log(`  xed-tui: found ${out.trim()} — ready.`);
        return;
      }
    } catch (_) {}
  }
  console.warn(
    "\n  xed-tui: Python 3.11+ not found.\n" +
    "  Install from: https://python.org/downloads\n" +
    "  Or via uv:    https://docs.astral.sh/uv/\n"
  );
}

check();
