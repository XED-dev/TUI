#!/usr/bin/env python3
"""
XED /TUI v1.23.0 (xed_tui_v1.py) — mutt-artiger TUI-Browser für ~/.claude/projects/ Sessions

Tastatur:
  ↑ ↓ / j k   Navigation
  Tab          Panel wechseln (Projekte ↔ Threads ↔ Reader ↔ Notizen)
  Enter        Thread öffnen / lesen
  PgUp PgDn    Im Reader blättern
  t            Thread umbenennen (Custom-Titel)
  d            Thread löschen (Bestätigung: "delete" tippen)
  a            Agent (Claude Code) mit dieser Session starten (--resume)
  o            /resume <uuid> in Zwischenablage — direkt in Claude Code einfügen
  e            Session-Notiz im Editor öffnen ($EDITOR oder nano)
  o            Session-Notiz in Standard-App öffnen (xdg-open, z.B. Typora)
  Ctrl+E       Einstellungen (Editor, Standard-App)
  c            Notiz in Zwischenablage (wl-copy / xclip / xsel)
  f            Nur Original-Session (Full — Vollbild)
  n            Nur Notizen (Vollbild)
  m            Move: Beide Panels — oder Seiten tauschen (wenn beide sichtbar)
  q / Esc      Zurück / Beenden
  ?            Hilfe

Starten:
  python dev/bin/xed-tui.py
"""

import curses
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import time
try:
    import termios
    import tty
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False  # Windows — print_paged falls back to plain print
from datetime import datetime
from pathlib import Path

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
VERSION = "v1.26.2"

# XED /TUI eigenes Territorium (außerhalb ~/.claude/ — Claude Code darf hier
# nichts anfassen). Später auch SQLite-DB unter db/, Cache, etc.
XED_TUI_HOME    = Path.home() / ".xed" / "tui"
XED_TUI_ARCHIVE = XED_TUI_HOME / "archive"
XED_TUI_STATE   = XED_TUI_HOME / "state"

# Kontinuitäts-Zustand (TUI-Wiederaufnahme nach Neustart).
CONTINUE_STATE_PATH = XED_TUI_STATE / "continue.json"
# v1.26 Migration: alter XDG-Pfad, wird per Lazy-Fallback noch gelesen.
_LEGACY_CONTINUE_STATE_PATH = Path.home() / ".local" / "share" / "xed-tui" / "continue.json"

# Virtuelles "ARCHIV"-Projekt: zeigt alle archivierten Sessions / Notizen.
# Wie in einer Klosterbibliothek — die kuratierte, dauerhafte Sammlung.
VIRTUAL_ARCHIV_NAME = "__ARCHIV__"
VIRTUAL_ARCHIV_PATH = CLAUDE_PROJECTS / VIRTUAL_ARCHIV_NAME
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)


def note_project(note_path: Path) -> Path:
    """Projekt-Verzeichnis einer Notiz herleiten: memory/<uuid>.md → <projekt>."""
    return note_path.parent.parent


def archive_path(proj_name: str, uuid: str) -> Path:
    """~/.xed/tui/archive/<proj>/<uuid>.jsonl"""
    return XED_TUI_ARCHIVE / proj_name / f"{uuid}.jsonl"


def archive_session(session: Path) -> bool:
    """Kopiert eine Live-JSONL ins Archiv (idempotent, nur wenn Quelle neuer).
    Gibt True zurück wenn tatsächlich kopiert wurde."""
    if session.suffix != ".jsonl" or not session.exists():
        return False
    proj_name = session.parent.name
    if proj_name == VIRTUAL_ARCHIV_NAME:
        return False
    dest = archive_path(proj_name, session.stem)
    if dest.exists() and session.stat().st_mtime <= dest.stat().st_mtime:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(session, dest)  # preserves mtime
    return True


def is_archived(path: Path) -> bool:
    """True wenn es eine Archiv-Kopie zur Session oder Notiz gibt."""
    if path.suffix == ".md":
        proj_name = note_project(path).name
    else:
        proj_name = path.parent.name
    if proj_name == VIRTUAL_ARCHIV_NAME:
        return False
    return archive_path(proj_name, path.stem).exists()


def archived_note_path(proj_name: str, uuid: str) -> Path:
    """~/.xed/tui/archive/<proj>/<uuid>.md — Schatten-Kopie der Notiz (v1.26)."""
    return XED_TUI_ARCHIVE / proj_name / f"{uuid}.md"


def archive_stats() -> dict:
    """Statistik über die XED-Bibliothek (Stats-Panel im ★ ARCHIV).

    Zählt Bände (.jsonl) und Katalogkarten (.md) aus ~/.xed/tui/archive/,
    summiert Bytes, bestimmt älteste/neueste mtime und Projekt-Verteilung.
    Kein Index, nur os.stat() + iterdir() — reicht bis in den hohen Tausender-Bereich.
    """
    stats = {"volumes": 0, "notes": 0, "bytes": 0,
             "oldest": None, "newest": None, "projects": []}
    if not XED_TUI_ARCHIVE.exists():
        return stats
    per_proj: dict[str, int] = {}
    for proj_dir in XED_TUI_ARCHIVE.iterdir():
        if not proj_dir.is_dir():
            continue
        vols = 0
        for f in proj_dir.iterdir():
            try:
                st = f.stat()
            except OSError:
                continue
            stats["bytes"] += st.st_size
            if stats["oldest"] is None or st.st_mtime < stats["oldest"]:
                stats["oldest"] = st.st_mtime
            if stats["newest"] is None or st.st_mtime > stats["newest"]:
                stats["newest"] = st.st_mtime
            if f.suffix == ".jsonl":
                stats["volumes"] += 1
                vols += 1
            elif f.suffix == ".md" and _UUID_RE.match(f.stem):
                stats["notes"] += 1
        if vols:
            per_proj[proj_dir.name] = vols
    stats["projects"] = sorted(per_proj.items(), key=lambda x: x[1], reverse=True)
    return stats


def _fmt_bytes(n: int) -> str:
    x = float(n)
    for unit in ("B", "K", "M", "G"):
        if x < 1024:
            return f"{x:.0f}{unit}" if unit == "B" else f"{x:.1f}{unit}"
        x /= 1024
    return f"{x:.1f}T"


def format_archive_stats(stats: dict, width: int) -> str:
    """Einzeilige Zusammenfassung der Bibliothek für die Stats-Zeile im ARCHIV."""
    if stats["volumes"] == 0 and stats["notes"] == 0:
        return "★ Bibliothek leer — noch keine Sessions archiviert"
    parts = [f"★ {stats['volumes']} Bände",
             f"{stats['notes']} Karten",
             _fmt_bytes(stats["bytes"])]
    if stats["oldest"] and stats["newest"]:
        d_old = datetime.fromtimestamp(stats["oldest"]).strftime("%y-%m-%d")
        d_new = datetime.fromtimestamp(stats["newest"]).strftime("%y-%m-%d")
        parts.append(f"{d_old}…{d_new}")
    n_proj = len(stats["projects"])
    if n_proj:
        top = stats["projects"][0]
        top_name = shorten_slug(top[0]) if len(top[0]) > 12 else top[0]
        if n_proj == 1:
            parts.append(f"1 Proj ({top_name})")
        else:
            parts.append(f"{n_proj} Proj · Top: {top_name} {top[1]}")
    line = " · ".join(parts)
    return line[: max(0, width - 2)]


def archive_note(notes_file: Path) -> bool:
    """Kopiert eine Per-Session-Notiz <uuid>.md ins Archiv (idempotent, mtime-preserve).
    Primärquelle bleibt memory/<uuid>.md (Auto-Memory-Brücke) — dies ist reine
    Schattenkopie für das Kronjuwel. Gibt True zurück wenn tatsächlich kopiert wurde."""
    if notes_file.suffix != ".md" or not notes_file.exists():
        return False
    if not _UUID_RE.match(notes_file.stem):
        return False    # Auto-Memory-Eintrag (user_/feedback_/project_/…), nicht unsere Sache
    proj_name = note_project(notes_file).name
    if proj_name == VIRTUAL_ARCHIV_NAME:
        return False
    dest = archived_note_path(proj_name, notes_file.stem)
    if dest.exists() and notes_file.stat().st_mtime <= dest.stat().st_mtime:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(notes_file, dest)
    return True


def resolved_jsonl(path: Path) -> Path | None:
    """Beste JSONL-Quelle für Leseoperationen — Archiv bevorzugt, Live-Fallback.
    - .md-Notiz: sucht Sibling-JSONL (Archiv bevorzugt, dann Live)
    - Live-.jsonl: Archiv bevorzugt, sonst die Datei selbst
    Gibt None zurück wenn es die Session weder live noch archiviert gibt (verwaist).
    """
    if path.suffix == ".md":
        proj = note_project(path)
        arch = archive_path(proj.name, path.stem)
        if arch.exists():
            return arch
        live = proj / f"{path.stem}.jsonl"
        return live if live.exists() else None
    # .jsonl (oder ähnliches)
    proj_name = path.parent.name
    if proj_name != VIRTUAL_ARCHIV_NAME:
        arch = archive_path(proj_name, path.stem)
        if arch.exists():
            return arch
    return path if path.exists() else None


def restore_session(archived_jsonl: Path, target_proj: Path) -> Path:
    """Kopiert eine archivierte JSONL zurück ins Live-Projekt-Verzeichnis.
    Setzt die mtime auf jetzt — Claude Codes Cleanup-Zähler wird zurückgesetzt."""
    target_proj.mkdir(parents=True, exist_ok=True)
    dest = target_proj / archived_jsonl.name
    shutil.copy2(archived_jsonl, dest)
    now = time.time()
    os.utime(dest, (now, now))
    return dest


def repair_custom_title_format(jsonl_path: Path) -> bool:
    """Repariert custom-title-Records, die von XED v1.25.0 / v1.26.0 im
    whitespace-gepaddeten Format geschrieben wurden. Claude Code und ZED
    erkennen diese Records in ihrer History-/Resume-UI nicht.

    Wenn der letzte custom-title-Record in der JSONL gepaddet ist (`{"type": ...`
    mit Leerzeichen nach `:` und `,`), wird ein frischer, kompakter Rewrite-Record
    mit demselben customTitle angehängt. Append-only, nicht-destruktiv.

    Gibt True zurück wenn repariert, False wenn nichts zu tun war.
    """
    if not jsonl_path.exists() or jsonl_path.suffix != ".jsonl":
        return False
    last_title = None
    last_session = None
    last_padded = False
    try:
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                if '"custom-title"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "custom-title" and obj.get("customTitle"):
                    last_title = obj["customTitle"]
                    last_session = obj.get("sessionId") or jsonl_path.stem
                    # Kompakt = startet mit '{"type":"custom-title"' (kein Leerzeichen).
                    last_padded = not line.startswith('{"type":"custom-title"')
    except OSError:
        return False
    if last_title is None or not last_padded:
        return False
    try:
        with open(jsonl_path, "a", encoding="utf-8") as f:
            record = {"type": "custom-title", "customTitle": last_title,
                      "sessionId": last_session}
            f.write(json.dumps(record, ensure_ascii=False,
                               separators=(",", ":")) + "\n")
    except OSError:
        return False
    return True


def get_all_notes() -> list[Path]:
    """Alle UUID-benannten .md-Notizen aus allen Projekten, neueste zuerst."""
    if not CLAUDE_PROJECTS.exists():
        return []
    notes = []
    for proj in CLAUDE_PROJECTS.iterdir():
        if not proj.is_dir() or proj.name == VIRTUAL_ARCHIV_NAME:
            continue
        mem_dir = proj / "memory"
        if not mem_dir.is_dir():
            continue
        for md in mem_dir.glob("*.md"):
            if _UUID_RE.match(md.stem):
                notes.append(md)
    return sorted(notes, key=lambda p: p.stat().st_mtime, reverse=True)

ANSI_ESCAPE = re.compile(
    r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'       # OSC (BEL- oder ST-Terminator) — z.B. Hyperlinks
    r'|\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])',  # CSI + simple 2-byte ESC
    re.DOTALL,
)

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


# ─── Markdown-Rendering-Helpers ───────────────────────────────────────────────

_HRULE_RE      = re.compile(r'^[-*=]{3,}$')
_TABLE_ROW_RE  = re.compile(r'^\s*\|')
_TABLE_SEP_RE  = re.compile(r'^\s*\|[\s\-:|]+\|')
_INLINE_MD_RE = re.compile(
    r'\*\*(.+?)\*\*'   # **bold**
    r'|(`+)(.+?)\2'    # `code` oder ``code`` — Backreference, gleiche Backtick-Anzahl
    r'|\*([^*\n]+)\*', # *italic*
    re.DOTALL,
)


def flush_table(raw_rows: list[str], width: int) -> list[tuple]:
    """Normalisiert Markdown-Tabelle auf gleichbreite Spalten."""
    parsed: list[list[str]] = []
    for row in raw_rows:
        cells = [c.strip() for c in row.strip().split('|')]
        # Führende und abschließende Leerstrings (vor/nach äußeren Pipes) entfernen
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]
        parsed.append(cells)

    if not parsed:
        return []

    n_cols = max(len(row) for row in parsed)

    # Separator-Erkennung: Zelle enthält nur -, :, Leerzeichen
    def _is_sep_row(cells: list[str]) -> bool:
        return all(
            not set(c).difference('-: ')
            for c in cells
        )

    # Sichtbare Länge: Markdown-Marker (**bold**, *italic*, `code`) rausrechnen
    def _vlen(cell: str) -> int:
        return sum(len(seg) for _, seg in parse_inline_md(cell))

    # Spaltenbreiten: Maximum der Nicht-Separator-Zeilen (sichtbare Länge)
    col_widths = [0] * n_cols
    for cells in parsed:
        if not _is_sep_row(cells):
            for i, cell in enumerate(cells[:n_cols]):
                col_widths[i] = max(col_widths[i], _vlen(cell))
    col_widths = [max(w, 1) for w in col_widths]

    def _hline(left: str, mid: str, right: str, fill: str) -> str:
        return left + mid.join(fill * (w + 2) for w in col_widths) + right

    result: list[tuple] = []
    first_data = True
    for cells in parsed:
        is_sep = _is_sep_row(cells)
        if is_sep:
            line = _hline('├', '┼', '┤', '─')
            result.append(('table_sep', line[:width]))
        else:
            if first_data:
                result.append(('table_sep', _hline('┌', '┬', '┐', '─')[:width]))
                first_data = False
            parts = [
                (cells[i] + ' ' * (col_widths[i] - _vlen(cells[i]))) if i < len(cells)
                else ' ' * col_widths[i]
                for i in range(n_cols)
            ]
            line = '│ ' + ' │ '.join(parts) + ' │'
            result.append(('table', line[:width]))
    if result:
        result.append(('table_sep', _hline('└', '┴', '┘', '─')[:width]))
    return result


def _classify_md_line(line: str, in_code: bool) -> str:
    """Markdown-Zeilentyp bestimmen — kind: h1/h2/h3/hrule/code_fence/code/quote/table/table_sep/gap/text."""
    # code_fence schlägt in_code — damit schließende ``` erkannt wird
    if line.startswith('```') or line.startswith('~~~'):
        return 'code_fence'
    # Table schlägt in_code — verhindert, dass hängende code_fences Tabellen verschlucken
    s = line.strip()
    if s.startswith('|'):
        inner = s.replace('|', '').replace('-', '').replace(':', '').replace(' ', '')
        return 'table_sep' if not inner else 'table'
    if in_code:
        return 'code'
    if not s:
        return 'gap'
    if s.startswith('# ') or s == '#':
        return 'h1'
    if s.startswith('## ') or s == '##':
        return 'h2'
    if s.startswith('### ') or s == '###':
        return 'h3'
    if _HRULE_RE.match(s):
        return 'hrule'
    if s.startswith('> ') or s == '>':
        return 'quote'
    return 'text'


def parse_inline_md(text: str) -> list[tuple[str, str]]:
    """Inline-Markdown → [(kind, text), …] — kinds: bold, code, italic, text.
    Unterstützt single- und double-backtick Code-Spans (CommonMark §6.1)."""
    segments: list[tuple[str, str]] = []
    pos = 0
    for m in _INLINE_MD_RE.finditer(text):
        if m.start() > pos:
            segments.append(('text', text[pos:m.start()]))
        if m.group(1) is not None:
            segments.append(('bold',   m.group(1)))
        elif m.group(3) is not None:
            segments.append(('code',   m.group(3).strip()))  # strip padding laut CommonMark
        else:
            segments.append(('italic', m.group(4)))
        pos = m.end()
    if pos < len(text):
        segments.append(('text', text[pos:]))
    return segments or [('text', text)]


def wrap_spans(spans: list[tuple[str, str]], width: int) -> list[list[tuple[str, str]]]:
    """Bricht Span-Liste span-bewusst an Wortgrenzen — kein Markdown-Marker wird gespalten."""
    lines: list[list[tuple[str, str]]] = [[]]
    col = 0
    for kind, seg in spans:
        for wi, word in enumerate(seg.split(' ')):
            if wi > 0 and col > 0:                       # Leerzeichen zwischen Wörtern
                cur = lines[-1]
                if cur and cur[-1][0] == kind:
                    cur[-1] = (kind, cur[-1][1] + ' ')
                else:
                    cur.append((kind, ' '))
                col += 1
            if not word:
                continue
            if col + len(word) > width and col > 0:       # Zeilenumbruch
                lines.append([])
                col = 0
            cur = lines[-1]
            if cur and cur[-1][0] == kind:
                cur[-1] = (kind, cur[-1][1] + word)
            else:
                cur.append((kind, word))
            col += len(word)
    return [line for line in lines if line]


def draw_md_line(win, y: int, x: int, text: str, base_attr: int, max_w: int,
                 inline_attrs: dict) -> None:
    """Zeile mit Inline-Markdown (bold/code/italic) zeichnen."""
    col = x
    limit = x + max_w
    for kind, seg in parse_inline_md(text):
        if col >= limit:
            break
        chunk = seg[:limit - col]
        attr = inline_attrs.get(kind, base_attr)
        try:
            win.addstr(y, col, chunk, attr)
        except curses.error:
            pass
        col += len(chunk)


def draw_table_row(win, y: int, x: int, text: str, max_w: int,
                   cell_attr: int, pipe_attr: int,
                   inline_attrs: dict | None = None) -> None:
    """Tabellen-Zeile mit gefärbten | Trennern und Inline-Markdown in Zellen."""
    col = x
    limit = x + max_w
    cell_buf = ''
    for ch in text:
        if col >= limit:
            break
        if ch in ('|', '│'):
            # Zell-Buffer mit Inline-Markdown rendern
            if cell_buf:
                if inline_attrs:
                    for kind, seg in parse_inline_md(cell_buf):
                        if col >= limit:
                            break
                        chunk = seg[:limit - col]
                        try:
                            win.addstr(y, col, chunk, inline_attrs.get(kind, cell_attr))
                        except curses.error:
                            pass
                        col += len(chunk)
                else:
                    chunk = cell_buf[:limit - col]
                    try:
                        win.addstr(y, col, chunk, cell_attr)
                    except curses.error:
                        pass
                    col += len(chunk)
                cell_buf = ''
            # Pipe-Zeichen zeichnen
            if col < limit:
                try:
                    win.addstr(y, col, ch, pipe_attr)
                except curses.error:
                    pass
                col += 1
        else:
            cell_buf += ch
    # Rest-Buffer leeren
    if cell_buf and col < limit:
        if inline_attrs:
            for kind, seg in parse_inline_md(cell_buf):
                if col >= limit:
                    break
                chunk = seg[:limit - col]
                try:
                    win.addstr(y, col, chunk, inline_attrs.get(kind, cell_attr))
                except curses.error:
                    pass
                col += len(chunk)
        else:
            try:
                win.addstr(y, col, cell_buf[:limit - col], cell_attr)
            except curses.error:
                pass


def get_key(win):
    """get_wch() wrapper: ASCII → int (kompatibel), Unicode-Chars → str, Sondertasten → int, Timeout → -1."""
    try:
        k = win.get_wch()
    except curses.error:
        return -1
    if isinstance(k, str):
        return ord(k) if ord(k) < 128 else k   # ASCII als int (bestehende Checks laufen weiter)
    return k


# ──────────────────────────────────────────────────────────────────────────────
# Daten-Layer
# ──────────────────────────────────────────────────────────────────────────────

def extract_text(content) -> str:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif c.get("type") == "tool_use":
                inp = c.get("input", {})
                name = c.get("name", "")
                desc = inp.get("description", inp.get("command", inp.get("pattern", "")))
                parts.append(f"[{name}: {str(desc)[:60]}]" if desc else f"[{name}]")
            elif c.get("type") == "tool_result":
                inner = c.get("content", "")
                if isinstance(inner, list):
                    inner = " ".join(x.get("text", "") for x in inner if isinstance(x, dict))
                parts.append(f"[→ {str(inner)[:80]}]")
        text = "\n".join(parts)
    else:
        text = str(content)
    text = re.sub(r"<command-name>(.*?)</command-name>", r"/\1", text)
    text = re.sub(r"<command-message>(.*?)</command-message>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<command-args>(.*?)</command-args>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def get_native_title(path: Path) -> str | None:
    """Liest den nativen /rename custom-title aus dem JSONL. Letzter Eintrag gewinnt."""
    result = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "custom-title" and obj.get("customTitle"):
                    result = obj["customTitle"].strip()
    except OSError:
        pass
    return result or None


def _first_md_heading(path: Path) -> str | None:
    """Erste nicht-leere Zeile einer .md-Datei (ohne #-Präfix) als Fallback-Titel."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip().lstrip("#").strip()
            if s:
                return s[:120]
    except OSError:
        pass
    return None


def first_human_title(path: Path) -> str:
    """Erste Human-Message als Fallback-Titel."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "user" and not obj.get("isMeta"):
                    text = extract_text(obj.get("message", {}).get("content", ""))
                    t = " ".join(text.split())
                    if t:
                        return t
    except OSError:
        pass
    return "(leer)"


def load_thread(path: Path) -> list[dict]:
    turns = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("isMeta"):
                    continue
                role = obj.get("type")
                if role not in ("user", "assistant"):
                    continue
                text = extract_text(obj.get("message", {}).get("content", ""))
                if text:
                    turns.append({"role": role, "text": text})
    except OSError:
        pass
    return turns


def get_session_cwd(path: Path) -> str | None:
    """Liest `cwd` aus der isMeta-Zeile des JSONL — für Claude Code --resume."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("isMeta") and "cwd" in obj:
                    return obj["cwd"]
    except OSError:
        pass
    return None


def get_all_projects() -> list[Path]:
    if not CLAUDE_PROJECTS.exists():
        return [VIRTUAL_ARCHIV_PATH]
    projects = [p for p in CLAUDE_PROJECTS.iterdir()
                if p.is_dir() and p.name != VIRTUAL_ARCHIV_NAME]
    projects.sort(key=lambda p: len(list(p.glob("*.jsonl"))), reverse=True)
    # Virtuelles NOTIZEN-Projekt immer an Position 0
    return [VIRTUAL_ARCHIV_PATH] + projects


def get_sessions(proj_dir: Path) -> list[Path]:
    if proj_dir.name == VIRTUAL_ARCHIV_NAME:
        return get_all_notes()
    return sorted(proj_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def format_mtime(path: Path) -> str:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    diff = (datetime.now() - mtime).days
    if diff == 0:
        return mtime.strftime("%H:%M")
    elif diff == 1:
        return "gestern"
    elif diff < 7:
        return f"vor {diff}d"
    else:
        return mtime.strftime("%d.%m.%y")


def shorten_slug(slug: str) -> str:
    parts = slug.lstrip("-").split("-")
    if len(parts) >= 2:
        return parts[-2] + "-" + parts[-1]
    return slug


def _state_proj_dir(proj_dir: Path) -> Path:
    """~/.xed/tui/state/<proj-slug>/ — XED-eigenes State-Verzeichnis pro Projekt (v1.26)."""
    return XED_TUI_STATE / proj_dir.name


def titles_path(proj_dir: Path) -> Path:
    """~/.xed/tui/state/<proj-slug>/titles.json (v1.26-Heimat)."""
    return _state_proj_dir(proj_dir) / "titles.json"


def _legacy_titles_path(proj_dir: Path) -> Path:
    """Vor v1.26: im memory/-Verzeichnis. Lazy-Fallback beim Lesen."""
    return proj_dir / "memory" / "titles.json"


def load_titles(proj_dir: Path) -> dict:
    p = titles_path(proj_dir)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    legacy = _legacy_titles_path(proj_dir)
    if legacy.exists():
        try:
            return json.loads(legacy.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_titles(proj_dir: Path, titles: dict):
    p = titles_path(proj_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")


def tags_path(proj_dir: Path) -> Path:
    """~/.xed/tui/state/<proj-slug>/tags.json (v1.26-Heimat)."""
    return _state_proj_dir(proj_dir) / "tags.json"


def _legacy_tags_path(proj_dir: Path) -> Path:
    return proj_dir / "memory" / "tags.json"


def load_tags(proj_dir: Path) -> dict:
    p = tags_path(proj_dir)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    legacy = _legacy_tags_path(proj_dir)
    if legacy.exists():
        try:
            return json.loads(legacy.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_tags(proj_dir: Path, tags: dict):
    p = tags_path(proj_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(tags, ensure_ascii=False, indent=2), encoding="utf-8")


def notes_sync_path(notes_file: Path) -> Path:
    """~/.xed/tui/state/<proj-slug>/<uuid>.sync — speichert synchronisierte Turn-Anzahl (v1.26)."""
    proj = note_project(notes_file)
    return _state_proj_dir(proj) / f"{notes_file.stem}.sync"


def _legacy_notes_sync_path(notes_file: Path) -> Path:
    return notes_file.with_suffix(".sync")


def read_sync_turns(notes_file: Path) -> int | None:
    """Gibt gespeicherte Turn-Anzahl zurück, None wenn kein .sync vorhanden."""
    p = notes_sync_path(notes_file)
    if p.exists():
        try:
            return int(p.read_text().strip())
        except Exception:
            return None
    legacy = _legacy_notes_sync_path(notes_file)
    if legacy.exists():
        try:
            return int(legacy.read_text().strip())
        except Exception:
            return None
    return None


def write_sync_turns(notes_file: Path, count: int):
    p = notes_sync_path(notes_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(count))


# ──────────────────────────────────────────────────────────────────────────────
# TUI State
# ──────────────────────────────────────────────────────────────────────────────

class State:
    def __init__(self):
        self.projects = get_all_projects()
        # Default: erstes echtes Projekt (Position 1), nicht das virtuelle NOTIZEN (Position 0).
        self.proj_idx = 1 if len(self.projects) > 1 else 0
        self.thread_idx = 0
        self.thread_scroll = 0
        self.reader_lines: list[tuple] = []
        self.reader_scroll = 0
        self.focus = "threads"
        self.split = 4          # 0 = Top ausgeblendet, 1-9 = n*5 Zeilen
        self.notes_lines: list[tuple] = []
        self.notes_scroll: int = 0
        self.view_mode: str = "both"    # "both" | "reader_only" | "notes_only"
        self.swapped: bool = False       # True = Notiz links, Reader rechts
        self._sessions_cache: dict[int, list] = {}
        self._title_cache: dict[Path, str] = {}
        self._notes_text_cache: dict[Path, str] = {}
        self._tokens_cache: dict[Path, tuple[int, int]] = {}
        self._tags_cache: dict[Path, list[str]] = {}
        self.force_redraw = False
        self.search_query: str = ""
        self.search_active: bool = False
        self.lang: str = "de"   # UI-Sprache: "de" | "en" | "fr" | "ja" | "es"
        self.editor_pref: str = "auto"   # "auto" | konkreter Befehl (z.B. "msedit", "nano")
        self.open_pref:   str = "auto"   # "auto" | konkreter App-Befehl (z.B. "typora")

    @property
    def status(self) -> str:
        return ("[?/H]Hlp [/]Find [#]Tag [T]Tit [D]Del [A]Agt [L]Lend"
                " [E]ed [U]pd [O]open [^E]Set [C]cp [S]Ses [F]Full [N]Not [M]mv [Q]")

    def is_virtual_archiv(self) -> bool:
        """True wenn das virtuelle NOTIZEN-Projekt aktiv ist."""
        return (0 <= self.proj_idx < len(self.projects)
                and self.projects[self.proj_idx].name == VIRTUAL_ARCHIV_NAME)

    def current_proj_for_session(self, path: Path) -> Path:
        """Projekt das zur aktuellen Session/Notiz gehört (virtuell-bewusst)."""
        if path is not None and path.suffix == ".md":
            return note_project(path)
        return self.projects[self.proj_idx]

    def proj_panel_w(self) -> int:
        """Optimale Breite des Projekte-Panels: längster Name + Rand."""
        if not self.projects:
            return 14
        def _nm(p: Path) -> str:
            return "ARCHIV" if p.name == VIRTUAL_ARCHIV_NAME else shorten_slug(p.name)
        max_name = max(len(_nm(p)) for p in self.projects)
        # " ● name   NNN" → border(1) + " ●  "(3) + name + "  NNN"(4) + border(1) = +9
        return max(14, max_name + 9)

    def sessions(self) -> list[Path]:
        idx = self.proj_idx
        if idx not in self._sessions_cache:
            # Alphabetisch absteigend nach Titel (z.B. "XED03..." vor "AI026..." vor "AI001...").
            raw = get_sessions(self.projects[idx])
            self._sessions_cache[idx] = sorted(
                raw, key=lambda p: self.title(p).lower(), reverse=True
            )
        return self._sessions_cache[idx]

    def session_tokens(self, path: Path) -> tuple[int, int]:
        """Gibt (input_tokens_last, output_tokens_total) zurück (gecacht).

        input_tokens_last  = input_tokens des letzten Assistant-Turns (Kontext-Größe)
        output_tokens_total = Summe aller output_tokens (tatsächlich generiert, kein Double-Count)
        """
        if path not in self._tokens_cache:
            # Archiv-bevorzugt: lies Tokens aus der besten verfügbaren Quelle.
            read_path = resolved_jsonl(path)
            if read_path is None:
                self._tokens_cache[path] = (0, 0)
                return (0, 0)
            inp_last = out_total = 0
            try:
                with open(read_path, encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        usage = (obj.get("message") or {}).get("usage") or obj.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        out_total += usage.get("output_tokens", 0)
                        inp = usage.get("input_tokens", 0)
                        if inp:
                            inp_last = inp   # letzter Wert gewinnt
            except OSError:
                pass
            self._tokens_cache[path] = (inp_last, out_total)
        return self._tokens_cache[path]

    def session_tags(self, path: Path) -> list[str]:
        """Tags für eine Session aus tags.json (gecacht). Virtual-Notes-bewusst."""
        if path not in self._tags_cache:
            if self.is_virtual_archiv():
                # Jede Notiz kann aus einem anderen Projekt stammen — einzeln laden.
                proj = self.current_proj_for_session(path)
                all_tags = load_tags(proj)
                self._tags_cache[path] = all_tags.get(path.stem, [])
            else:
                all_tags = load_tags(self.projects[self.proj_idx])
                for s in self.sessions():
                    if s not in self._tags_cache:
                        self._tags_cache[s] = all_tags.get(s.stem, [])
        return self._tags_cache.get(path, [])

    def tag_current(self, tags_str: str) -> str:
        """Setzt Tags für die aktuelle Session. tags_str = komma-getrennt, # optional."""
        path = self.current_session()
        if not path:
            return "Keine Session ausgewählt."
        tags = [t.strip().lstrip("#").lower() for t in tags_str.split(",") if t.strip()]
        proj = self.current_proj_for_session(path)
        all_tags = load_tags(proj)
        if tags:
            all_tags[path.stem] = tags
        else:
            all_tags.pop(path.stem, None)
        save_tags(proj, all_tags)
        self._tags_cache[path] = tags
        return "Tags: " + (" ".join(f"#{t}" for t in tags) if tags else "(keine)")

    def _notes_text(self, path: Path) -> str:
        """Gibt den rohen Notiz-Text für eine Session zurück (gecacht, ANSI-bereinigt)."""
        if path not in self._notes_text_cache:
            if path.suffix == ".md":
                notes_file = path
            else:
                notes_file = self.projects[self.proj_idx] / "memory" / f"{path.stem}.md"
            try:
                raw = notes_file.read_text(encoding="utf-8") if notes_file.exists() else ""
            except OSError:
                raw = ""
            self._notes_text_cache[path] = strip_ansi(raw).lower()
        return self._notes_text_cache[path]

    def filtered_sessions(self) -> list[Path]:
        sessions = self.sessions()
        if not self.search_query:
            return sessions
        q = self.search_query.lower().strip()
        if q.startswith("#"):
            tag = q[1:]
            if not tag:
                return sessions          # nur "#" getippt → noch kein Filter
            return [s for s in sessions if tag in self.session_tags(s)]
        # v1.26: Ranking — Treffer im Titel zählen 10×, Notiz-Treffer 1×.
        scored: list[tuple[int, Path]] = []
        for s in sessions:
            t_hits = self.title(s).lower().count(q)
            n_hits = self._notes_text(s).count(q)
            score = t_hits * 10 + n_hits
            if score > 0:
                scored.append((score, s))
        # Desc nach Score; Reihenfolge bei Gleichstand = Original (stable sort erhält sessions()-Order).
        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored]

    def search_snippet(self, path: Path, width: int = 36) -> str | None:
        """v1.26: kurzer Kontext-String um den ersten Notiz-Treffer, oder None.
        Nur wenn Suchterm nicht schon im Title steckt und nicht Tag-Filter."""
        q = self.search_query.lower().strip()
        if not q or q.startswith("#"):
            return None
        if q in self.title(path).lower():
            return None
        text = self._notes_text(path)
        idx = text.find(q)
        if idx < 0:
            return None
        pad = max(0, (width - len(q)) // 2)
        start = max(0, idx - pad)
        end = min(len(text), idx + len(q) + pad)
        snippet = re.sub(r"\s+", " ", text[start:end]).strip()
        left = "…" if start > 0 else ""
        right = "…" if end < len(text) else ""
        return f"«{left}{snippet}{right}»"

    def title(self, path: Path) -> str:
        # Priorität: /rename (JSONL) > [t] (titles.json) > erste Human-Message / Notiz-Überschrift
        #
        # v1.26.2 Bugfix: Native-Title (custom-title-Record) IMMER aus der Live-JSONL
        # lesen — sie ist die Source-of-Truth für aktuelle Renames. Das Archiv ist
        # eine Schatten-Kopie und kann ältere custom-title-Records enthalten,
        # solange seit dem letzten [e]/[u]/[U] umbenannt wurde. Vorher las XED den
        # Title aus resolved_jsonl() (archiv-bevorzugt) und zeigte deshalb nach
        # einem Restart wieder den veralteten Stand.
        # Content-Reader-Pfade (first_human_title, _build_reader_lines, …) bleiben
        # archiv-bevorzugt (Cleanup-Resilienz nach Claude Codes 90-Tage-Lifecycle).
        if path not in self._title_cache:
            live_jsonl = (note_project(path) / f"{path.stem}.jsonl"
                          if path.suffix == ".md" else path)
            title_src   = live_jsonl if live_jsonl.exists() else resolved_jsonl(path)
            content_src = resolved_jsonl(path)
            if path.suffix == ".md":
                proj = note_project(path)
                native   = get_native_title(title_src) if title_src is not None else None
                tui      = load_titles(proj).get(path.stem)
                fallback = first_human_title(content_src) if content_src is not None else _first_md_heading(path)
                self._title_cache[path] = native or tui or fallback or "(verwaiste Notiz)"
            else:
                native  = get_native_title(title_src) if title_src is not None else None
                tui     = load_titles(self.projects[self.proj_idx]).get(path.stem)
                fallback = first_human_title(content_src) if content_src is not None else "(leer)"
                self._title_cache[path] = native or tui or fallback
        return self._title_cache[path]

    def current_session(self) -> Path | None:
        sess = self.filtered_sessions()
        if sess and 0 <= self.thread_idx < len(sess):
            return sess[self.thread_idx]
        return None

    def _build_reader_lines(self, path: Path, width: int) -> list[tuple]:
        # Archiv-bevorzugt lesen. Bei verwaister Notiz: Inhalt als synthetischer Turn.
        src = resolved_jsonl(path)
        if src is not None:
            turns = load_thread(src)
        elif path.suffix == ".md":
            try:
                content = strip_ansi(path.read_text(encoding="utf-8"))
            except OSError:
                content = "(Notiz nicht lesbar)"
            turns = [{"role": "user",
                      "text": f"(verwaiste Notiz — Original-Session wurde gelöscht)\n\n{content}"}]
        else:
            turns = []
        lines = []
        w = max(width - 4, 20)
        for turn in turns:
            if turn["role"] == "user":
                lines.append(("header_user", "▶ YOU"))
            else:
                lines.append(("header_claude", "◀ CLAUDE"))
            lines.append(("sep", "─" * w))
            in_code = False
            table_buf: list[str] = []
            for raw_line in turn["text"].split("\n"):
                kind = _classify_md_line(raw_line, in_code)
                if kind in ('table', 'table_sep'):
                    table_buf.append(raw_line)
                    continue
                if table_buf:
                    lines.extend(flush_table(table_buf, w))
                    table_buf = []
                if kind == 'code_fence':
                    in_code = not in_code
                    lines.append(('code_fence', raw_line[:w]))
                    continue
                if kind == 'gap':
                    lines.append(("gap", ""))
                    continue
                if kind == 'code':
                    lines.append(('code', raw_line[:w]))
                    continue
                if kind in ('h1', 'h2', 'h3'):
                    lines.append((kind, raw_line[:w]))
                    continue
                if kind == 'hrule':
                    lines.append(('hrule', '─' * min(w, 60)))
                    continue
                if kind == 'quote':
                    for wl in wrap_spans(parse_inline_md(raw_line), w) or [[('text', raw_line[:w])]]:
                        lines.append(('quote', wl))
                    continue
                # 'text'
                for wl in wrap_spans(parse_inline_md(raw_line), w) or [[('text', raw_line[:w])]]:
                    lines.append(("text", wl))
            if table_buf:
                lines.extend(flush_table(table_buf, w))
            lines.append(("gap", ""))
        return lines

    def _build_notes_lines(self, path: Path, width: int) -> list[tuple]:
        """Notizen aus memory/<uuid>.md — ANSI-bereinigt, Markdown-gerendert."""
        if path.suffix == ".md":
            notes_file = path
        else:
            proj = self.projects[self.proj_idx]
            notes_file = proj / "memory" / f"{path.stem}.md"
        lines = []
        w = max(width - 4, 10)
        if not notes_file.exists():
            lines.append(("notes_hint", "[e] edit = create notes"))
            return lines
        raw = strip_ansi(notes_file.read_text(encoding="utf-8").strip())
        if not raw:
            lines.append(("notes_hint", "[e] edit = create notes"))
            return lines
        in_code = False
        table_buf: list[str] = []
        for raw_line in raw.split("\n"):
            stripped = raw_line.strip()
            # Sync-Format-Sonderzeichen (aus _sync_notes) — vor table_buf prüfen
            if stripped in ("## YOU", "## CLAUDE"):
                if table_buf:
                    lines.extend(flush_table(table_buf, w))
                    table_buf = []
                kind_hdr = "notes_header_user" if stripped == "## YOU" else "notes_header_claude"
                lines.append((kind_hdr, stripped))
                continue
            kind = _classify_md_line(raw_line, in_code)
            if kind in ('table', 'table_sep'):
                table_buf.append(raw_line)
                continue
            if table_buf:
                lines.extend(flush_table(table_buf, w))
                table_buf = []
            if kind == 'code_fence':
                in_code = not in_code
                lines.append(('code_fence', raw_line[:w]))
                continue
            if kind == 'gap':
                lines.append(("notes", ""))
                continue
            if kind == 'code':
                lines.append(('code', raw_line[:w]))
                continue
            if kind in ('h1', 'h2', 'h3'):
                lines.append((kind, raw_line[:w]))
                continue
            if kind == 'hrule':
                lines.append(('hrule', '─' * min(w, 60)))
                continue
            if kind == 'quote':
                for wl in wrap_spans(parse_inline_md(raw_line), w) or [[('text', raw_line[:w])]]:
                    lines.append(('quote', wl))
                continue
            # 'text'
            for wl in wrap_spans(parse_inline_md(raw_line), w) or [[('text', raw_line[:w])]]:
                lines.append(("notes", wl))
        if table_buf:
            lines.extend(flush_table(table_buf, w))
        return lines

    def open_reader(self, total_w: int):
        """Lädt Thread + wechselt Fokus zum Reader."""
        path = self.current_session()
        if not path:
            return
        rw, nw = self._panel_widths(total_w)
        self.reader_lines = self._build_reader_lines(path, rw)
        self.notes_lines  = self._build_notes_lines(path, nw)
        self.reader_scroll = 0
        self.notes_scroll  = 0
        self.focus = "reader"

    def preview_reader(self, total_w: int):
        """Aktualisiert Reader + Notes ohne Fokuswechsel."""
        path = self.current_session()
        if not path:
            self.reader_lines = []
            self.notes_lines  = []
            return
        rw, nw = self._panel_widths(total_w)
        self.reader_lines = self._build_reader_lines(path, rw)
        self.notes_lines  = self._build_notes_lines(path, nw)
        self.reader_scroll = 0

    def refresh_notes(self, total_w: int):
        """Nur Notes neu laden (nach Editor), Scroll beibehalten."""
        path = self.current_session()
        if not path:
            return
        _, nw = self._panel_widths(total_w)
        self.notes_lines = self._build_notes_lines(path, nw)
        self.notes_scroll = 0

    def _panel_widths(self, total_w: int) -> tuple[int, int]:
        """Gibt (reader_w, notes_w) für Textumbruch zurück — je nach view_mode + swapped."""
        if self.view_mode == "reader_only":
            return total_w, max(10, total_w // 3)
        if self.view_mode == "notes_only":
            return max(20, total_w // 3), total_w
        # "both": linkes Panel 2/3, rechtes 1/3
        left_w  = max(20, total_w * 2 // 3)
        right_w = max(10, total_w - left_w)
        if self.swapped:
            return right_w, left_w   # reader rechts (1/3), notes links (2/3)
        return left_w, right_w       # reader links (2/3), notes rechts (1/3)

    def refresh(self) -> str:
        """Projekte + Sessions neu von Disk laden."""
        old_proj_name = self.projects[self.proj_idx].name if self.projects else None
        old_session = self.current_session()   # aktuelle Session merken für B.2
        self.projects = get_all_projects()
        # Projekt-Index wiederherstellen
        if old_proj_name:
            for i, p in enumerate(self.projects):
                if p.name == old_proj_name:
                    self.proj_idx = i
                    break
            else:
                self.proj_idx = 0
        self._sessions_cache.clear()
        self._title_cache.clear()
        self._notes_text_cache.clear()
        self._tokens_cache.clear()
        self._tags_cache.clear()
        # Cursor-Position wiederherstellen (selbe Session nach Reload)
        self.thread_idx = 0
        if old_session:
            for i, s in enumerate(self.sessions()):
                if s == old_session:
                    self.thread_idx = i
                    break
        self.thread_scroll = 0
        self.reader_lines = []
        self.notes_lines = []
        self.force_redraw = True
        self.search_query = ""
        self.search_active = False
        return "  Aktualisiert."

    def rename_current(self, new_title: str) -> str:
        path = self.current_session()
        if not path:
            return "Kein Thread ausgewählt."
        proj = self.current_proj_for_session(path)
        # 1) Nativ ins JSONL schreiben (wie /rename) — nur wenn JSONL existiert
        jsonl = proj / f"{path.stem}.jsonl" if path.suffix == ".md" else path
        if jsonl.exists():
            try:
                with open(jsonl, "a", encoding="utf-8") as f:
                    record = {"type": "custom-title", "customTitle": new_title,
                              "sessionId": path.stem}
                    # Kompaktes Format (separators=(",", ":")) — Claude Code und ZED
                    # erkennen custom-title-Records nur ohne Whitespace-Padding (v1.26.1).
                    f.write(json.dumps(record, ensure_ascii=False,
                                       separators=(",", ":")) + "\n")
            except OSError:
                pass
        # 2) titles.json aktualisieren (TUI-Fallback)
        titles = load_titles(proj)
        titles[path.stem] = new_title
        save_titles(proj, titles)
        self._title_cache[path] = new_title
        return f"Umbenannt → {new_title[:50]}"

    def delete_current(self) -> str:
        path = self.current_session()
        if not path:
            return "Kein Thread ausgewählt."
        name = path.name
        proj = self.current_proj_for_session(path)
        # Im NOTIZEN-Virtual: nur die .md-Datei löschen, JSONL bleibt.
        path.unlink()
        if path.suffix == ".jsonl":
            uuid_dir = path.parent / path.stem
            if uuid_dir.exists() and uuid_dir.is_dir():
                shutil.rmtree(uuid_dir)
        titles = load_titles(proj)
        titles.pop(path.stem, None)
        save_titles(proj, titles)
        self._sessions_cache.pop(self.proj_idx, None)
        self._title_cache.pop(path, None)
        self._notes_text_cache.pop(path, None)
        sessions = self.filtered_sessions()
        self.thread_idx = min(self.thread_idx, max(0, len(sessions) - 1))
        self.reader_lines = []
        return f"Gelöscht: {name}"

    def memory_path(self) -> Path | None:
        proj = self.projects[self.proj_idx]
        if proj.name == VIRTUAL_ARCHIV_NAME:
            # Im virtuellen NOTIZEN-Projekt ist MEMORY.md kontextabhängig
            # von der aktuellen Session — falls eine ausgewählt ist, nimm deren Projekt.
            sess = self.current_session()
            if sess is None:
                return None
            proj = self.current_proj_for_session(sess)
        mem_dir = proj / "memory"
        mem_dir.mkdir(exist_ok=True)
        p = mem_dir / "MEMORY.md"
        if not p.exists():
            p.write_text(f"# Memory — {proj.name}\n\nErstellt: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
                         encoding="utf-8")
        return p

    def notes_path(self, session: Path | None = None) -> Path | None:
        """Notiz-Datei zur Session (oder zur aktuellen Session): memory/<uuid>.md"""
        path = session if session is not None else self.current_session()
        if not path:
            return None
        if path.suffix == ".md":
            # Virtuell: Session IST bereits die Notiz.
            return path
        proj = self.current_proj_for_session(path)
        mem_dir = proj / "memory"
        mem_dir.mkdir(exist_ok=True)
        return mem_dir / f"{path.stem}.md"

    def prefill_notes(self, notes_file: Path, width: int, session: Path | None = None):
        """Füllt leere Notiz-Datei mit dem Session-Transcript als Markdown vor.
        Vor dem Prefill wird die Live-JSONL ins XED-Archiv kopiert (→ Bibliothek)."""
        path = session if session is not None else self.current_session()
        if not path:
            return
        # In ARCHIV-Virtual: path ist bereits die .md-Datei — kein Prefill nötig.
        if path.suffix == ".md":
            return
        # Bibliotheks-Prinzip: JSONL bei Notiz-Erstellung ins Archiv kopieren.
        archive_session(path)
        title = self.title(path)
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        turns = load_thread(resolved_jsonl(path) or path)

        lines = [
            f"# {title}",
            f"Session: {path.stem}",
            f"Datum:   {mtime}",
            f"Projekt: {self.current_proj_for_session(path).name}",
            "",
            "---",
            "",
        ]
        for turn in turns:
            if turn["role"] == "user":
                lines.append("## YOU")
            else:
                lines.append("## CLAUDE")
            lines.append("")
            lines.append(turn["text"])
            lines.append("")
            lines.append("---")
            lines.append("")

        notes_file.write_text("\n".join(lines), encoding="utf-8")
        write_sync_turns(notes_file, len(turns))   # Sync-Status setzen
        archive_note(notes_file)                   # Katalogkarte ins Archiv

    def append_new_turns(self, notes_file: Path, session: Path | None = None) -> str:
        """Hängt Turns die seit dem letzten Sync neu hinzukamen an die Notiz-Datei an.
        Ruft dabei archive_session() auf — Bibliothek und Katalog bleiben synchron."""
        path = session if session is not None else self.current_session()
        if not path:
            return "  Keine Session ausgewählt."
        if path.suffix == ".md":
            # ARCHIV-Virtual: path IST die Notiz — kein JSONL-Sync möglich.
            return "  Sync nicht verfügbar im ARCHIV-Modus."
        # Bibliotheks-Prinzip: JSONL bei jedem Notiz-Update ins Archiv kopieren.
        archive_session(path)
        synced = read_sync_turns(notes_file)
        turns = load_thread(resolved_jsonl(path) or path)
        if synced is None:
            # Alte Notiz ohne .sync — initialisieren: alle aktuellen Turns als bereits synced markieren
            write_sync_turns(notes_file, len(turns))
            return f"  Sync aktiviert — {len(turns)} Turns registriert. Notiz aktuell."
        new_turns = turns[synced:]
        if not new_turns:
            return "  Notiz aktuell — keine neuen Turns."
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = ["", "---", "", f"## Update: {ts}", "", "---", ""]
        for turn in new_turns:
            lines.append("## YOU" if turn["role"] == "user" else "## CLAUDE")
            lines.append("")
            lines.append(turn["text"])
            lines.append("")
            lines.append("---")
            lines.append("")
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))
        write_sync_turns(notes_file, len(turns))
        archive_note(notes_file)   # Katalogkarte aktualisieren
        return f"  {len(new_turns)} neue Turn(s) angehängt."

    def update_all_notes(self, width: int) -> str:
        """Batch-Update aller Notizen im aktuellen Projekt (oder über alle Projekte in NOTIZEN-Virtual).

        - Fehlende Notizen werden mit Transcript-Prefill angelegt.
        - Bestehende Notizen mit .sync bekommen neue Turns angehängt, wenn das
          JSONL neuer ist als die Notiz.
        - Ohne .sync (alte Notizen) werden übersprungen — Respekt vor manueller Pflege.
        - ALLE Sessions mit Live-JSONL werden ins XED-Archiv kopiert (auch aktuelle).
        """
        sessions = self.sessions()
        if not sessions:
            return "  Keine Sessions im aktuellen Projekt."
        created = updated = current_ = skipped = orphan = archived = 0
        notes_archived = 0
        titles_repaired = 0
        for sess in sessions:
            # Quelle (JSONL) und Ziel (.md) je nach Kontext bestimmen.
            if sess.suffix == ".md":
                # ARCHIV-Virtual: sess IST die Notiz, JSONL-Quelle archiv-bevorzugt.
                jsonl_source = resolved_jsonl(sess)
                if jsonl_source is None:
                    orphan += 1
                    continue
                target = sess
            else:
                target = self.notes_path(sess)
                if target is None:
                    continue
                jsonl_source = sess

            # Bibliothek auffüllen: auch Sessions ohne Notiz-Änderung archivieren,
            # solange noch eine Live-JSONL existiert.
            if sess.suffix != ".md" and archive_session(sess):
                archived += 1

            if not target.exists() or target.stat().st_size == 0:
                self.prefill_notes(target, width, session=jsonl_source)
                created += 1
                continue

            if read_sync_turns(target) is None:
                # Alte Notiz ohne .sync — nicht automatisch anfassen.
                skipped += 1
                continue
            if jsonl_source.stat().st_mtime <= target.stat().st_mtime:
                current_ += 1
                continue
            msg = self.append_new_turns(target, session=jsonl_source)
            if "Turn(s) angehängt" in msg:
                updated += 1
            else:
                current_ += 1

        # Katalogkarten ins Archiv ziehen (idempotent per mtime-Check).
        for sess in sessions:
            target = sess if sess.suffix == ".md" else self.notes_path(sess)
            if target and target.exists() and archive_note(target):
                notes_archived += 1

        # Pre-v1.26.1 custom-title-Records reparieren (whitespace → kompakt).
        # Claude Code / ZED History-UIs lesen nur das kompakte Format.
        for sess in sessions:
            live = (note_project(sess) / f"{sess.stem}.jsonl"
                    if sess.suffix == ".md" else sess)
            if live.exists() and repair_custom_title_format(live):
                titles_repaired += 1
                self._title_cache.pop(sess, None)

        # Caches invalidieren (Notizen-Text, Session-Reihenfolge).
        self._notes_text_cache.clear()
        self._sessions_cache.pop(self.proj_idx, None)

        parts = []
        if created:
            parts.append(f"{created} neu")
        if updated:
            parts.append(f"{updated} erneuert")
        if current_:
            parts.append(f"{current_} aktuell")
        if archived:
            parts.append(f"{archived} Bände")
        if notes_archived:
            parts.append(f"{notes_archived} Karten")
        if titles_repaired:
            parts.append(f"{titles_repaired} Titel repariert")
        if skipped:
            parts.append(f"{skipped} ohne Sync")
        if orphan:
            parts.append(f"{orphan} verwaist")
        if not parts:
            parts = ["nichts zu tun"]
        return "  Bibliothek: " + " · ".join(parts)

    def backup_current(self) -> str:
        path = self.current_session()
        if not path:
            return "Kein Thread ausgewählt."
        if path.suffix == ".md":
            # NOTIZEN-Virtual: Notiz backupen (nicht JSONL).
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = path.parent / f"{path.stem}_backup_{ts}.md"
            shutil.copy2(path, dest)
            return f"Backup: {dest.name}"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = path.parent / f"{path.stem}_backup_{ts}.jsonl"
        shutil.copy2(path, dest)
        return f"Backup: {dest.name}"


# ──────────────────────────────────────────────────────────────────────────────
# Dialoge
# ──────────────────────────────────────────────────────────────────────────────

def input_dialog(stdscr, title: str, prompt: str, prefill: str = "") -> str | None:
    """Einzeiliges Eingabe-Popup. Esc → None, Enter → Text."""
    h, w = stdscr.getmaxyx()
    dw = min(72, w - 4)
    dh = 6
    y0 = max(0, (h - dh) // 2)
    x0 = max(0, (w - dw) // 2)
    win = curses.newwin(dh, dw, y0, x0)
    win.keypad(True)   # Sondertasten (←→ Home End Backspace) korrekt empfangen
    curses.curs_set(1)

    buf = list(prefill)
    cursor = len(buf)
    cursor_moved = False   # True sobald Cursor-Taste gedrückt → kein Auto-Clear mehr

    while True:
        win.erase()
        win.border()
        win.addstr(0, 2, f" {title} ", curses.color_pair(1) | curses.A_BOLD)
        try:
            win.addstr(2, 2, prompt[:dw - 4], curses.color_pair(4))
        except curses.error:
            pass

        field_w = dw - 4
        # Fenster auf Cursor-Position
        view_start = max(0, cursor - field_w + 1)
        display = "".join(buf)[view_start:view_start + field_w]
        try:
            win.addstr(4, 2, display.ljust(field_w), curses.color_pair(9))
            win.move(4, 2 + min(cursor - view_start, field_w - 1))
        except curses.error:
            pass
        win.refresh()

        key = get_key(win)
        if key == 27:
            curses.curs_set(0)
            return None
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            curses.curs_set(0)
            return "".join(buf)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor > 0:
                buf.pop(cursor - 1)
                cursor -= 1
        elif key == curses.KEY_DC:
            if cursor < len(buf):
                buf.pop(cursor)
        elif key == curses.KEY_LEFT:
            cursor = max(0, cursor - 1)
            cursor_moved = True   # ← Navigation → kein Auto-Clear
        elif key == curses.KEY_RIGHT:
            cursor = min(len(buf), cursor + 1)
            cursor_moved = True   # → Navigation → kein Auto-Clear
        elif key == curses.KEY_HOME:
            cursor = 0            # Home → Auto-Clear bleibt aktiv
        elif key == curses.KEY_END:
            cursor = len(buf)     # End → cursor != 0, Auto-Clear irrelevant
        elif isinstance(key, str):                        # Unicode (Umlaute, etc.)
            if cursor == 0 and buf and not cursor_moved:
                buf.clear()
            buf.insert(cursor, key)
            cursor += 1
        elif 32 <= key <= 126:                            # ASCII
            if cursor == 0 and buf and not cursor_moved:  # Am Anfang ohne nav → leeren
                buf.clear()
            buf.insert(cursor, chr(key))
            cursor += 1


def confirm_dialog(stdscr, title: str, msg: str, word: str = "delete") -> bool:
    """Bestätigung durch Eingabe eines Schlüsselworts."""
    result = input_dialog(stdscr, title, f'{msg}  [tippe "{word}" + Enter]')
    return result == word


def copy_to_clipboard(text: str) -> str:
    """Kopiert Text in die Zwischenablage. Gibt Status-Meldung zurück.

    xclip/xsel laufen als Daemon weiter → subprocess.run() blockiert für immer.
    Lösung: Popen + stdin schreiben + wait(timeout=2).
    Timeout = Daemon läuft = OK (wl-copy hingegen beendet sich sofort).
    """
    data = text.encode("utf-8")
    errors = []
    for cmd in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            try:
                proc.stdin.write(data)
                proc.stdin.close()
            except BrokenPipeError:
                errors.append(f"{cmd[0]}: broken pipe")
                continue
            try:
                proc.wait(timeout=2)
                if proc.returncode == 0:
                    return f"Notiz kopiert  ({cmd[0]})"
                err = proc.stderr.read().decode(errors="replace").strip()
                errors.append(f"{cmd[0]}: rc={proc.returncode} {err}")
            except subprocess.TimeoutExpired:
                # Daemon läuft im Hintergrund (normal für xclip) → Erfolg
                return f"Notiz kopiert  ({cmd[0]})"
        except FileNotFoundError:
            errors.append(f"{cmd[0]}: nicht gefunden")
    return "Clipboard-Fehler: " + " | ".join(errors)


# ──────────────────────────────────────────────────────────────────────────────
# --continue  State-Persistenz
# ──────────────────────────────────────────────────────────────────────────────

def save_continue_state(state: "State") -> None:
    """Aktuellen TUI-Zustand in CONTINUE_STATE_PATH speichern."""
    sess = state.current_session()
    data = {
        "project":       state.projects[state.proj_idx].name if state.projects else None,
        "session_uuid":  sess.stem if sess else None,
        "reader_scroll": state.reader_scroll,
        "notes_scroll":  state.notes_scroll,
        "split":         state.split,
        "view_mode":     state.view_mode,
        "swapped":       state.swapped,
        "search_query":  state.search_query,
        "focus":         state.focus,
        "lang":          state.lang,
        "editor_pref":   state.editor_pref,
        "open_pref":     state.open_pref,
    }
    CONTINUE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTINUE_STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_continue_state() -> dict | None:
    """Gespeicherten Zustand laden — None wenn Datei fehlt oder defekt.
    v1.26: Primary ~/.xed/tui/state/, Fallback auf alten XDG-Pfad."""
    if CONTINUE_STATE_PATH.exists():
        try:
            return json.loads(CONTINUE_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    if _LEGACY_CONTINUE_STATE_PATH.exists():
        try:
            return json.loads(_LEGACY_CONTINUE_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def apply_continue_state(state: "State", data: dict) -> None:
    """Gespeicherten Zustand auf State-Objekt anwenden."""
    proj_name = data.get("project")
    if proj_name:
        for i, p in enumerate(state.projects):
            if p.name == proj_name:
                state.proj_idx = i
                state._sessions_cache.clear()
                break
    uuid = data.get("session_uuid")
    if uuid:
        for i, s in enumerate(state.sessions()):
            if s.stem == uuid:
                state.thread_idx = i
                break
    state.reader_scroll = data.get("reader_scroll", 0)
    state.notes_scroll  = data.get("notes_scroll",  0)
    state.split         = data.get("split",         4)
    state.view_mode     = data.get("view_mode",     "both")
    state.swapped       = data.get("swapped",       False)
    state.search_query  = data.get("search_query",  "")
    state.focus         = data.get("focus",         "threads")
    state.lang          = data.get("lang",          "de")
    state.editor_pref   = data.get("editor_pref",   "auto")
    state.open_pref     = data.get("open_pref",     "auto")


# ──────────────────────────────────────────────────────────────────────────────
# Zeichnen
# ──────────────────────────────────────────────────────────────────────────────

# Color-Maps für Markdown-Rendering — befüllt durch init_colors() nach start_color()
_READER_COLOR_MAP:  dict[str, int] = {}
_READER_INLINE:     dict[str, int] = {}
_NOTES_COLOR_MAP:   dict[str, int] = {}
_NOTES_INLINE:      dict[str, int] = {}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN,   -1)
    curses.init_pair(2, curses.COLOR_WHITE,  -1)
    curses.init_pair(3, curses.COLOR_GREEN,  -1)   # Tags
    curses.init_pair(4, curses.COLOR_WHITE,  -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_CYAN,   -1)
    curses.init_pair(7, curses.COLOR_BLACK,  curses.COLOR_WHITE)
    curses.init_pair(9, curses.COLOR_WHITE,  curses.COLOR_BLUE)
    cp = curses.color_pair
    _READER_COLOR_MAP.update({
        "header_user":   cp(5) | curses.A_BOLD,
        "header_claude": cp(6) | curses.A_BOLD,
        "sep":           cp(2),
        "h1":            cp(6) | curses.A_BOLD,
        "h2":            cp(6) | curses.A_BOLD,
        "h3":            cp(5) | curses.A_BOLD,
        "hrule":         cp(2),
        "code_fence":    cp(3),
        "code":          cp(3),
        "quote":         cp(5),
        "table":         cp(4),
        "table_sep":     cp(1),
        "text":          cp(4),
        "gap":           cp(4),
    })
    _READER_INLINE.update({
        "bold":   cp(5) | curses.A_BOLD,
        "code":   cp(3),
        "italic": cp(4) | getattr(curses, 'A_ITALIC', curses.A_UNDERLINE),
        "text":   cp(4),
    })
    _NOTES_COLOR_MAP.update({
        "notes":               cp(4),
        "notes_hint":          cp(5) | curses.A_BOLD,
        "notes_header_user":   cp(5) | curses.A_BOLD,
        "notes_header_claude": cp(6) | curses.A_BOLD,
        "h1":            cp(6) | curses.A_BOLD,
        "h2":            cp(6) | curses.A_BOLD,
        "h3":            cp(5) | curses.A_BOLD,
        "hrule":         cp(2),
        "code_fence":    cp(3),
        "code":          cp(3),
        "quote":         cp(5),
        "table":         cp(4),
        "table_sep":     cp(1),
        "text":          cp(4),
        "gap":           cp(4),
    })
    _NOTES_INLINE.update(_READER_INLINE)


def draw_border(win, title: str, active: bool):
    attr = curses.color_pair(1) | curses.A_BOLD if active else curses.color_pair(2)
    try:
        win.border()
        win.addstr(0, 2, f" {title} ", attr)
    except curses.error:
        pass


def draw_projects(win, state: State):
    draw_border(win, "Projekte", state.focus == "projects")
    h, w = win.getmaxyx()
    for i, proj in enumerate(state.projects):
        y = i + 1
        if y >= h - 1:
            break
        if proj.name == VIRTUAL_ARCHIV_NAME:
            name = "ARCHIV"[:w - 6]
            mem_mark = "★"
            sess_count = len(get_all_notes())
        else:
            name = shorten_slug(proj.name)[:w - 6]
            mem_mark = "●" if (proj / "memory").exists() else " "
            sess_count = len(list(proj.glob("*.jsonl")))
        line = f" {mem_mark} {name:<{w-9}} {sess_count:>3}"[:w-2]
        attr = curses.color_pair(9) | curses.A_BOLD if i == state.proj_idx else curses.color_pair(2)
        try:
            win.addstr(y, 1, line, attr)
        except curses.error:
            pass


def draw_threads(win, state: State):
    sessions = state.filtered_sessions()
    if state.search_query:
        total = len(state.sessions())
        sfx = "_" if state.search_active else ""
        border_title = f"Sessions /{state.search_query}{sfx} ({len(sessions)}/{total})"
    else:
        border_title = "Sessions"
    draw_border(win, border_title, state.focus == "threads")
    # VERSION rechts in der Border-Zeile
    h, w = win.getmaxyx()
    ver = f" XED /TUI {VERSION} "
    if len(border_title) + len(ver) + 10 < w:
        attr = curses.color_pair(1) | curses.A_BOLD if state.focus == "threads" else curses.color_pair(2)
        try:
            win.addstr(0, w - len(ver) - 1, ver, attr)
        except curses.error:
            pass
    virtual = state.is_virtual_archiv()
    # Stats-Zeile nur im virtuellen ★ ARCHIV (nimmt eine Session-Zeile weg).
    stats_row = 1 if virtual else 0
    visible = h - 2 - stats_row

    if virtual:
        try:
            win.addstr(1, 1, format_archive_stats(archive_stats(), w - 2).ljust(w - 2),
                       curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

    if state.thread_idx < state.thread_scroll:
        state.thread_scroll = state.thread_idx
    if state.thread_idx >= state.thread_scroll + visible:
        state.thread_scroll = state.thread_idx - visible + 1

    tag_col_w = 11 if w >= 70 else 0   # " #hvd #bug" — nur bei breitem Terminal

    for row, i in enumerate(range(state.thread_scroll, state.thread_scroll + visible)):
        y = row + 1 + stats_row
        if i >= len(sessions):
            break
        s = sessions[i]
        nr = f"#{i+1:<3}"
        date = format_mtime(s)
        _, out_tok = state.session_tokens(s)
        tok_str = f"{out_tok/1000:>4.0f}k" if out_tok >= 1000 else f"{out_tok:>4}t"
        title = state.title(s)
        tags = state.session_tags(s)
        archived_ok = is_archived(s)

        # Bibliotheks-Marker: grüner Punkt = im Archiv, leer = nur Live/ungesichert
        mark = "●" if archived_ok else " "
        prefix = f" {nr} {date:<8} {mark} "
        suffix = f" {tok_str}"
        if tag_col_w > 0:
            tag_text = " ".join(f"#{t}" for t in tags[:2])[:tag_col_w - 1]
            tag_display = f" {tag_text:<{tag_col_w - 1}}"
        else:
            tag_display = ""
        title_w = max(4, w - len(prefix) - len(suffix) - len(tag_display) - 2)
        if virtual:
            # Projekt-Kürzel in fixer Breite (8 Zeichen) → nachfolgende Spalte bleibt bündig.
            proj_tag = f"{shorten_slug(note_project(s).name):<8.8}"
            full_title = f"[{proj_tag}] {title}"
        else:
            full_title = title
        # v1.26: bei Notiz-Match (nicht im Title) kurzes Kontext-Snippet anhängen.
        snippet = state.search_snippet(s) if state.search_query else None
        if snippet and title_w > len(full_title) + 6:
            combo = f"{full_title}  {snippet}"
            title_short = combo[:title_w]
        else:
            title_short = full_title[:title_w]

        is_sel = (i == state.thread_idx)
        row_attr  = curses.color_pair(9) | curses.A_BOLD if is_sel else curses.color_pair(4)
        tag_attr  = curses.color_pair(9) | curses.A_BOLD if is_sel else curses.color_pair(3)
        mark_attr = curses.color_pair(9) | curses.A_BOLD if is_sel else curses.color_pair(3)
        pre = f"{prefix}{title_short:<{title_w}}"
        try:
            win.addstr(y, 1, pre, row_attr)
            # Marker nachträglich grün überzeichnen (an bekannter Position im prefix)
            if archived_ok:
                mark_x = 1 + len(f" {nr} {date:<8} ")
                win.addstr(y, mark_x, mark, mark_attr)
            x = 1 + len(pre)
            if tag_display:
                win.addstr(y, x, tag_display, tag_attr)
                x += len(tag_display)
            win.addstr(y, x, suffix[:w - x - 1], row_attr)
        except curses.error:
            pass

    if len(sessions) > visible:
        bar_h = max(1, visible * visible // len(sessions))
        bar_y = state.thread_scroll * (visible - bar_h) // max(1, len(sessions) - visible)
        for r in range(visible):
            attr = curses.color_pair(1) if bar_y <= r < bar_y + bar_h else curses.color_pair(2)
            try:
                win.addstr(1 + stats_row + r, w - 2, "│", attr)
            except curses.error:
                pass


def draw_reader(win, state: State):
    path = state.current_session()
    title = state.title(path) if path else "—"
    h, w = win.getmaxyx()
    label = "Full Reader" if state.view_mode == "reader_only" else "Reader"
    max_title = max(1, w - len(label) - 8)   # label + ": "(2) + border+spaces(6)
    draw_border(win, f"{label}: {title[:max_title]}", state.focus == "reader")
    lines = state.reader_lines
    visible = h - 2
    state.reader_scroll = min(state.reader_scroll, max(0, len(lines) - visible))

    cp = curses.color_pair

    for row in range(visible):
        idx = state.reader_scroll + row
        if idx >= len(lines):
            break
        kind, text = lines[idx]
        y = row + 1
        base_attr = _READER_COLOR_MAP.get(kind, cp(4))
        try:
            if kind == 'table':
                draw_table_row(win, y, 2, text[:w-4], w-4, cp(4), cp(1) | curses.A_BOLD, _READER_INLINE)
            elif kind in ('text', 'quote', 'h1', 'h2', 'h3'):
                if isinstance(text, list):          # Pre-wrapped Span-Liste aus wrap_spans
                    col = 2
                    limit = w - 2
                    for sk, st in text:
                        if col >= limit:
                            break
                        chunk = st[:limit - col]
                        win.addstr(y, col, chunk, _READER_INLINE.get(sk, base_attr))
                        col += len(chunk)
                else:
                    draw_md_line(win, y, 2, text[:w-4], base_attr, w-4, _READER_INLINE)
            else:
                win.addstr(y, 2, text[:w-4], base_attr)
        except curses.error:
            pass

    if lines:
        pct = int((state.reader_scroll + visible) * 100 / len(lines))
        info = f" {state.reader_scroll+1}-{min(state.reader_scroll+visible,len(lines))}/{len(lines)} ({pct}%) "
        try:
            win.addstr(h - 1, w - len(info) - 1, info, curses.color_pair(1))
        except curses.error:
            pass


def draw_status(win, state: State, msg: str = ""):
    _, w = win.getmaxyx()
    text = (msg if msg else state.status)[:w - 1]
    try:
        win.addstr(0, 0, text.ljust(w - 1), curses.color_pair(7))
    except curses.error:
        pass




def quit_confirm_dialog(stdscr) -> bool:
    """ESC-Bestätigung: Enter = Quit, ESC = Abbrechen."""
    h, w = stdscr.getmaxyx()
    msg = "  Press Enter to quit XED /TUI — or ESC to cancel  "
    dw = min(len(msg) + 4, w - 2)
    dh = 3
    y0 = max(0, (h - dh) // 2)
    x0 = max(0, (w - dw) // 2)
    win = curses.newwin(dh, dw, y0, x0)
    win.border()
    win.addstr(0, 2, " Quit? ", curses.color_pair(1) | curses.A_BOLD)
    try:
        win.addstr(1, 2, msg[:dw - 4])
    except curses.error:
        pass
    win.refresh()
    while True:
        k = win.getch()
        if k in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            return True
        if k == 27:
            return False


def show_settings(stdscr, state):
    """Einstellungen-Overlay (Ctrl+E): Editor und Standard-App konfigurieren."""
    h, w = stdscr.getmaxyx()
    bh = 9
    bw = min(56, w)
    y0 = max(0, (h - bh) // 2)
    x0 = max(0, (w - bw) // 2)

    # Working copies
    editor_val = state.editor_pref
    open_val   = state.open_pref
    editor_idx = (_EDITOR_PRESETS.index(editor_val)
                  if editor_val in _EDITOR_PRESETS else -1)
    open_idx   = (_OPEN_PRESETS.index(open_val)
                  if open_val in _OPEN_PRESETS else -1)

    focus = 0  # 0 = [E] Editor, 1 = [O] App

    while True:
        win = curses.newwin(bh, bw, y0, x0)
        win.keypad(True)
        win.erase()
        win.border()
        win.addstr(0, 2, " Einstellungen ", curses.color_pair(1) | curses.A_BOLD)

        inner = bw - 10  # display width for value

        e_disp = (editor_val if editor_idx == -1 else _EDITOR_PRESETS[editor_idx])
        o_disp = (open_val   if open_idx   == -1 else _OPEN_PRESETS[open_idx])

        e_line = f"  [E] Editor   \u2190  {e_disp:<{inner}}\u2192"
        o_line = f"  [O] App      \u2190  {o_disp:<{inner}}\u2192"

        try:
            win.addstr(2, 2, e_line[:bw - 4],
                       curses.A_REVERSE if focus == 0 else 0)
        except curses.error:
            pass
        try:
            win.addstr(4, 2, o_line[:bw - 4],
                       curses.A_REVERSE if focus == 1 else 0)
        except curses.error:
            pass

        hint = "  \u2191\u2193 wechseln \u00b7 \u2190\u2192 Preset \u00b7 Enter=Pfad \u00b7 q Ok"
        try:
            win.addstr(bh - 2, 2, hint[:bw - 4], curses.color_pair(7))
        except curses.error:
            pass

        win.refresh()
        k = win.getch()

        if k in (ord("q"), ord("Q"), 27):
            state.editor_pref = (editor_val if editor_idx == -1
                                 else _EDITOR_PRESETS[editor_idx])
            state.open_pref   = (open_val   if open_idx   == -1
                                 else _OPEN_PRESETS[open_idx])
            return
        elif k in (curses.KEY_UP, ord("k")):
            focus = 0
        elif k in (curses.KEY_DOWN, ord("j")):
            focus = 1
        elif k == curses.KEY_RIGHT:
            if focus == 0:
                editor_idx = 0 if editor_idx == -1 else (editor_idx + 1) % len(_EDITOR_PRESETS)
                editor_val = _EDITOR_PRESETS[editor_idx]
            else:
                open_idx = 0 if open_idx == -1 else (open_idx + 1) % len(_OPEN_PRESETS)
                open_val = _OPEN_PRESETS[open_idx]
        elif k == curses.KEY_LEFT:
            if focus == 0:
                editor_idx = (len(_EDITOR_PRESETS) - 1 if editor_idx == -1
                              else (editor_idx - 1) % len(_EDITOR_PRESETS))
                editor_val = _EDITOR_PRESETS[editor_idx]
            else:
                open_idx = (len(_OPEN_PRESETS) - 1 if open_idx == -1
                            else (open_idx - 1) % len(_OPEN_PRESETS))
                open_val = _OPEN_PRESETS[open_idx]
        elif k in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            label   = "Editor-Befehl" if focus == 0 else "App-Befehl"
            prefill = editor_val if focus == 0 else open_val
            new_val = input_dialog(stdscr, "Einstellungen", f"{label}:", prefill=prefill)
            if new_val is not None:
                new_val = new_val.strip() or prefill
                if focus == 0:
                    editor_val = new_val
                    editor_idx = (_EDITOR_PRESETS.index(new_val)
                                  if new_val in _EDITOR_PRESETS else -1)
                else:
                    open_val = new_val
                    open_idx = (_OPEN_PRESETS.index(new_val)
                                if new_val in _OPEN_PRESETS else -1)


def show_help(stdscr, state):
    h, w = stdscr.getmaxyx()
    lang_idx = LANGS.index(state.lang) if state.lang in LANGS else 0

    # Width and height stay constant across all languages (use largest text)
    _max_content_w = max(
        max((len(ln) for ln in HELP_TEXTS[lg].strip().split("\n")), default=40)
        for lg in LANGS
    )
    _max_lines = max(len(HELP_TEXTS[lg].strip().split("\n")) for lg in LANGS)
    _lang_bar_sample = "  " + "  ".join(f"[●{lg.upper()}]" for lg in LANGS) + "  "
    _bw = min(max(_max_content_w + 6, len(_lang_bar_sample) + 4), w)
    _bh = min(_max_lines + 5, h)

    while True:  # language loop
        lines = HELP_TEXTS[LANGS[lang_idx]].strip().split("\n")

        # Lang-bar: "[●DE] [ EN] [ FR] [ JA] [ ES]"
        tags = [f"[●{lg.upper()}]" if i == lang_idx else f"[ {lg.upper()}]"
                for i, lg in enumerate(LANGS)]

        bw = _bw
        bh = _bh
        x0 = max(0, (w - bw) // 2)
        visible = max(1, bh - 5)   # border(2) + lang_bar(1) + empty(1) + footer(1)
        scroll = 0

        while True:  # scroll loop
            y0 = max(0, (h - bh) // 2)
            win = curses.newwin(bh, bw, y0, x0)
            win.keypad(True)   # Arrow keys → KEY_* constants, not raw ESC sequences
            win.erase()
            win.border()
            win.addstr(0, 2, " Help / Hilfe ", curses.color_pair(1) | curses.A_BOLD)

            # Lang-bar (row 1)
            bar_x = 2
            for i, tag in enumerate(tags):
                attr = (curses.color_pair(1) | curses.A_BOLD
                        if i == lang_idx else curses.color_pair(2))
                try:
                    win.addstr(1, bar_x, tag, attr)
                except curses.error:
                    pass
                bar_x += len(tag) + 2

            # Content (row 3 onward, row 2 is empty separator)
            for i, line in enumerate(lines[scroll:scroll + visible]):
                try:
                    win.addstr(i + 3, 3, line[:bw - 4])
                except curses.error:
                    pass

            # Footer (row bh-2)
            at_end = scroll + visible >= len(lines)
            if at_end:
                more = " ←→ Sprache · Ende — beliebige Taste schließt "
                attr = curses.color_pair(1) | curses.A_BOLD
            else:
                more = " ←→ Sprache · SPC/↓ weiter · q schließen "
                attr = curses.color_pair(7) | curses.A_BOLD
            try:
                win.addstr(bh - 2, 3, more[:bw - 4], attr)
            except curses.error:
                pass

            win.refresh()
            k = win.getch()

            if k in (ord("q"), ord("Q"), 27):
                state.lang = LANGS[lang_idx]
                return
            elif k == curses.KEY_RIGHT:
                lang_idx = (lang_idx + 1) % len(LANGS)
                tags = [f"[●{lg.upper()}]" if i == lang_idx else f"[ {lg.upper()}]"
                        for i, lg in enumerate(LANGS)]
                break   # break scroll loop → language loop redraws
            elif k == curses.KEY_LEFT:
                lang_idx = (lang_idx - 1) % len(LANGS)
                tags = [f"[●{lg.upper()}]" if i == lang_idx else f"[ {lg.upper()}]"
                        for i, lg in enumerate(LANGS)]
                break   # break scroll loop → language loop redraws
            elif ord("1") <= k <= ord("5"):
                lang_idx = k - ord("1")
                tags = [f"[●{lg.upper()}]" if i == lang_idx else f"[ {lg.upper()}]"
                        for i, lg in enumerate(LANGS)]
                break   # break scroll loop → language loop redraws
            elif k in (ord(" "), curses.KEY_DOWN, ord("j"), curses.KEY_NPAGE,
                       curses.KEY_ENTER, ord("\n"), ord("\r")):
                if at_end:
                    state.lang = LANGS[lang_idx]
                    return
                scroll = min(scroll + visible, max(0, len(lines) - visible))
            elif k in (curses.KEY_UP, ord("k"), curses.KEY_PPAGE):
                scroll = max(0, scroll - visible)
            elif at_end:
                state.lang = LANGS[lang_idx]
                return

        # Only reached via break (language change) — clear old window before redraw
        win.erase()
        win.refresh()


# ──────────────────────────────────────────────────────────────────────────────
# Hauptschleife
# ──────────────────────────────────────────────────────────────────────────────

def make_windows(h, w, split: int, view_mode: str = "both", swapped: bool = False, proj_w: int = 18):
    """
    split=0     → Top ausgeblendet, untere Area füllt alles
    split=1-9   → thread_h = split * 5, Rest = untere Area
    view_mode   → "both" (60/40), "reader_only", "notes_only"
    swapped     → True = Notiz links, Reader rechts (nur bei "both")
    proj_w      → Breite des Projekte-Panels (dynamisch, passend zum längsten Namen)
    """
    proj_w = min(proj_w, w // 3)   # nie mehr als 1/3 des Terminals
    left_w  = max(20, w * 2 // 3)   # linkes Panel immer 2/3
    right_w = max(10, w - left_w)   # rechtes Panel immer 1/3

    if split == 0:
        thread_h = 0
        reader_h = h - 1
        proj_win   = None
        thread_win = None
    else:
        thread_h = min(split * 5, h - 4)
        reader_h = max(3, h - thread_h - 1)
        proj_win   = curses.newwin(thread_h, proj_w,     0, 0)
        thread_win = curses.newwin(thread_h, w - proj_w, 0, proj_w)

    if view_mode == "reader_only":
        reader_win = curses.newwin(reader_h, w, thread_h, 0)
        notes_win  = None
    elif view_mode == "notes_only":
        reader_win = None
        notes_win  = curses.newwin(reader_h, w, thread_h, 0)
    else:  # "both" — linkes Panel stets 2/3, rechtes 1/3
        if swapped:
            notes_win  = curses.newwin(reader_h, left_w,  thread_h, 0)
            reader_win = curses.newwin(reader_h, right_w, thread_h, left_w)
        else:
            reader_win = curses.newwin(reader_h, left_w,  thread_h, 0)
            notes_win  = curses.newwin(reader_h, right_w, thread_h, left_w)

    status_win = curses.newwin(1, w, h - 1, 0)
    return proj_win, thread_win, reader_win, notes_win, status_win, proj_w, reader_h, thread_h


def draw_notes(win, state: State):
    path = state.current_session()
    title = state.title(path) if path else "—"
    h, w = win.getmaxyx()
    max_title = max(1, w - 15)   # "Notizen: "(9) + border+spaces(6) overhead
    draw_border(win, f"Notizen: {title[:max_title]}", state.focus == "notes")
    lines = state.notes_lines
    visible = h - 2
    state.notes_scroll = min(state.notes_scroll, max(0, len(lines) - visible))

    cp = curses.color_pair

    for row in range(visible):
        idx = state.notes_scroll + row
        if idx >= len(lines):
            break
        kind, text = lines[idx]
        y = row + 1
        base_attr = _NOTES_COLOR_MAP.get(kind, cp(4))
        try:
            if kind == 'table':
                draw_table_row(win, y, 2, text[:w-4], w-4, cp(4), cp(1) | curses.A_BOLD, _NOTES_INLINE)
            elif kind in ('notes', 'text', 'quote', 'h1', 'h2', 'h3'):
                if isinstance(text, list):          # Pre-wrapped Span-Liste aus wrap_spans
                    col = 2
                    limit = w - 2
                    for sk, st in text:
                        if col >= limit:
                            break
                        chunk = st[:limit - col]
                        win.addstr(y, col, chunk, _NOTES_INLINE.get(sk, base_attr))
                        col += len(chunk)
                else:
                    draw_md_line(win, y, 2, text[:w-4], base_attr, w-4, _NOTES_INLINE)
            else:
                win.addstr(y, 2, text[:w-4], base_attr)
        except curses.error:
            pass

    if lines and len(lines) > visible:
        pct = int((state.notes_scroll + visible) * 100 / len(lines))
        info = f" {state.notes_scroll+1}-{min(state.notes_scroll+visible,len(lines))}/{len(lines)} ({pct}%) "
        try:
            win.addstr(h - 1, w - len(info) - 1, info, curses.color_pair(1))
        except curses.error:
            pass


def main(stdscr, continue_data: dict | None = None):
    curses.curs_set(0)
    stdscr.timeout(100)
    curses.flushinp()   # Residual-Input (z.B. Ctrl+R vom vorherigen Prozess) verwerfen
    init_colors()
    state = State()
    if continue_data:
        apply_continue_state(state, continue_data)
    flash_msg = ""
    flash_timer = 0

    stdscr.clear()
    stdscr.refresh()

    h, w = stdscr.getmaxyx()
    proj_win, thread_win, reader_win, notes_win, status_win, proj_w, reader_h, thread_h = make_windows(h, w, state.split, state.view_mode, state.swapped, state.proj_panel_w())
    last_layout = (h, w, state.split, state.view_mode, state.swapped)

    # Initial-Preview: Inhalt laden unabhängig vom gespeicherten Fokus
    if state.sessions():
        if state.view_mode == "both":
            _np = state.notes_path()
            state.swapped = _np is not None and _np.exists() and _np.stat().st_size > 0
        state.preview_reader(w)

    while True:
        h, w = stdscr.getmaxyx()

        if h < 10 or w < 40:
            stdscr.clear()
            stdscr.addstr(0, 0, "Terminal zu klein (min 40×10)")
            stdscr.refresh()
            if stdscr.getch() in (ord("q"), 27):
                break
            continue

        cur_layout = (h, w, state.split, state.view_mode, state.swapped)
        if cur_layout != last_layout or state.force_redraw:
            stdscr.clear()
            stdscr.refresh()
            proj_win, thread_win, reader_win, notes_win, status_win, proj_w, reader_h, thread_h = make_windows(h, w, state.split, state.view_mode, state.swapped, state.proj_panel_w())
            last_layout = cur_layout
            state.force_redraw = False
            # Bei split=0 Fokus auf Reader/Notizen zwingen
            if state.split == 0 and state.focus in ("projects", "threads"):
                state.focus = "reader" if state.view_mode != "notes_only" else "notes"
        # Fokus-Korrektur bei view_mode-Wechsel
        if state.view_mode == "reader_only" and state.focus == "notes":
            state.focus = "reader"
        elif state.view_mode == "notes_only" and state.focus == "reader":
            state.focus = "notes"

        # Auto-preview: Reader-Lines laden wenn focus auf threads und noch leer
        if state.focus == "threads" and not state.reader_lines and state.sessions():
            if state.view_mode == "both":
                np = state.notes_path()
                has_note = np is not None and np.exists() and np.stat().st_size > 0
                state.swapped = has_note
            state.preview_reader(w)


        if proj_win:
            proj_win.erase()
        if thread_win:
            thread_win.erase()
        if reader_win:
            reader_win.erase()
        if notes_win:
            notes_win.erase()
        status_win.erase()

        if proj_win:
            draw_projects(proj_win, state)
        if thread_win:
            draw_threads(thread_win, state)
        if reader_win:
            draw_reader(reader_win, state)
        if notes_win:
            draw_notes(notes_win, state)
        if state.search_active:
            _smsg = f"  /{state.search_query}_  [Enter] öffnen · [Esc] löschen · ↑↓ navigieren"
        elif state.search_query:
            _smsg = f"  Filter: /{state.search_query}  [/] ändern · [s] zurücksetzen"
        else:
            _smsg = flash_msg if flash_timer > 0 else ""
        draw_status(status_win, state, _smsg)
        if flash_timer > 0:
            flash_timer -= 1

        if proj_win:
            proj_win.noutrefresh()
        if thread_win:
            thread_win.noutrefresh()
        if reader_win:
            reader_win.noutrefresh()
        if notes_win:
            notes_win.noutrefresh()
        status_win.noutrefresh()
        curses.doupdate()

        key = get_key(stdscr)
        if key == -1:
            continue

        # Jede Taste räumt eine stehengebliebene Flash-Message sofort weg —
        # der Key-Handler darf direkt danach ggf. eine neue setzen.
        flash_timer = 0

        focus = state.focus

        # ── Such-Modus ────────────────────────────────────────────────────────
        if state.search_active:
            if key in (ord("q"), ord("Q")):
                break
            elif key == 27:                                      # ESC: löschen + beenden
                state.search_active = False
                state.search_query = ""
                state.thread_idx = 0
                state.thread_scroll = 0
                state.preview_reader(w)
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):  # Enter: bestätigen
                state.search_active = False
                if state.filtered_sessions():
                    state.open_reader(w)
            elif key in (curses.KEY_UP, ord("k")):
                if state.thread_idx > 0:
                    state.thread_idx -= 1
                    state.preview_reader(w)
            elif key in (curses.KEY_DOWN, ord("j")):
                if state.thread_idx < len(state.filtered_sessions()) - 1:
                    state.thread_idx += 1
                    state.preview_reader(w)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                state.search_query = state.search_query[:-1]
                state.thread_idx = 0
                state.thread_scroll = 0
                state.preview_reader(w)
            elif isinstance(key, str):                  # Unicode (Umlaute etc.)
                state.search_query += key
                state.thread_idx = 0
                state.thread_scroll = 0
                state.preview_reader(w)
            elif 32 <= key <= 126:                      # ASCII
                state.search_query += chr(key)
                state.thread_idx = 0
                state.thread_scroll = 0
                state.preview_reader(w)
            continue

        # ── Universell ────────────────────────────────────────────────────────
        if key in (ord("q"), ord("Q")):
            save_continue_state(state)
            break  # sofort beenden, aus jedem Panel

        elif key == 27:
            if quit_confirm_dialog(stdscr):
                save_continue_state(state)
                break
            state.force_redraw = True

        elif key == 18:  # Ctrl+R — Hot-Reload: State speichern + neu starten mit --continue
            save_continue_state(state)
            curses.endwin()
            script = str(Path(__file__).resolve())
            os.execv(sys.executable, [sys.executable, script, "--continue"])

        elif key == 5:  # Ctrl+E — Einstellungen
            show_settings(stdscr, state)
            save_continue_state(state)
            state.force_redraw = True

        elif key in (ord("?"), ord("h"), ord("H")):
            show_help(stdscr, state)
            state.force_redraw = True

        elif key in (ord("\t"), curses.KEY_F6):
            if state.view_mode == "reader_only":
                cycle = {"projects": "threads", "threads": "reader", "reader": "projects", "notes": "projects"}
            elif state.view_mode == "notes_only":
                cycle = {"projects": "threads", "threads": "notes", "notes": "projects", "reader": "projects"}
            else:
                cycle = {
                    "projects": "threads",
                    "threads":  "reader" if state.reader_lines else "projects",
                    "reader":   "notes",
                    "notes":    "projects",
                }
            state.focus = cycle.get(focus, "threads")

        elif isinstance(key, int) and ord("0") <= key <= ord("9"):
            state.split = key - ord("0")
            label = "Top ausgeblendet" if state.split == 0 else f"Top = {state.split * 5} Zeilen"
            flash_msg = f"  Layout: {label}  (Taste 1-9 anpassen, 0 = ausblenden)"
            flash_timer = 35

        elif key in (ord("c"), ord("C")):
            np = state.notes_path()
            if np and np.exists() and np.stat().st_size > 0:
                text = strip_ansi(np.read_text(encoding="utf-8"))
                flash_msg = "  " + copy_to_clipboard(text)
            else:
                flash_msg = "  No notes yet  ([e] = create notes)"
            flash_timer = 40

        elif key in (ord("t"), ord("T")):
            path = state.current_session()
            if path:
                current_title = state.title(path)
                new_title = input_dialog(stdscr, "Title", "New title:", prefill=current_title)
                state.force_redraw = True
                if new_title and new_title != current_title:
                    flash_msg = "  " + state.rename_current(new_title)
                    flash_timer = 40

        elif key in (ord("r"), ord("R")):
            path = state.current_session()
            if path:
                resume_cmd = f"/resume {path.stem}"
                result = copy_to_clipboard(resume_cmd)
                flash_msg = "  " + result.replace("Notiz kopiert", f"Copied: {resume_cmd}")
            else:
                flash_msg = "  No session selected."
            flash_timer = 40

        elif key in (ord("f"), ord("F")):
            if state.view_mode == "reader_only":
                state.view_mode = "both"
                state.focus = "threads"
                state.preview_reader(w)
                flash_msg = "  Both panels active"
            else:
                state.view_mode = "reader_only"
                state.focus = "reader"
                state.preview_reader(w)
                flash_msg = "  Full Reader — [f] = back to both panels"
            flash_timer = 35

        elif key in (ord("n"), ord("N")):
            if state.view_mode == "notes_only":
                state.view_mode = "both"
                state.focus = "threads"
                state.preview_reader(w)
                flash_msg = "  Both panels active"
            else:
                state.view_mode = "notes_only"
                state.focus = "notes"
                state.preview_reader(w)
                flash_msg = "  Notes (fullscreen) — [n] = back to both panels"
            flash_timer = 35

        elif key in (ord("m"), ord("M")):
            if state.view_mode in ("reader_only", "notes_only"):
                state.view_mode = "both"
                state.preview_reader(w)
                flash_msg = "  Both panels active"
            else:
                state.swapped = not state.swapped
                state.preview_reader(w)   # Inhalt auf neue Panelbreite umbrechen
                flash_msg = "  Panels swapped: " + ("Notes left | Reader right" if state.swapped else "Reader left | Notes right")
            # Fokus auf das größere (linke) Panel
            state.focus = "notes" if state.swapped else "reader"
            flash_timer = 30

        elif key in (ord("d"), ord("D")):
            path = state.current_session()
            if path:
                title_preview = state.title(path)[:40]
                if confirm_dialog(stdscr, "Delete", f'"{title_preview}"'):
                    flash_msg = "  " + state.delete_current()
                    flash_timer = 40
                    state.preview_reader(w)
                else:
                    flash_msg = "  Cancelled."
                    flash_timer = 20
                state.force_redraw = True

        elif key in (ord("e"), ord("E")):
            # Open notes file for current session (memory/<uuid>.md)
            target = state.notes_path() or state.memory_path()
            if target and (not target.exists() or target.stat().st_size == 0):
                # Neue Notiz → Transcript als Prefill
                state.prefill_notes(target, w)
            elif target and target.exists():
                # Bestehende Notiz → neue Turns anhängen wenn JSONL neuer + .sync vorhanden
                sess = state.current_session()
                if (sess and read_sync_turns(target) is not None
                        and sess.stat().st_mtime > target.stat().st_mtime):
                    state.append_new_turns(target)
            if state.editor_pref == "auto":
                _msedit_home = Path.home() / ".local" / "bin" / "msedit"
                editor = (os.environ.get("EDITOR")
                          or shutil.which("msedit")
                          or (str(_msedit_home) if _msedit_home.exists() else None)
                          or "nano")
            else:
                editor = state.editor_pref
            curses.endwin()
            subprocess.run([editor, str(target)])
            stdscr.clear()
            stdscr.refresh()
            state.force_redraw = True
            # Reload notes panel after returning from editor
            state._notes_text_cache.clear()
            state.refresh_notes(w)
            state.notes_scroll = len(state.notes_lines)   # ans Ende scrollen
            state.focus = "notes"
            flash_msg = f"  Notes saved: {target.name}  [{editor}]"
            flash_timer = 30

        elif key in (ord("o"), ord("O")):
            # [O] Notiz in Standard-App öffnen (xdg-open → z.B. Typora)
            target = state.notes_path() or state.memory_path()
            if target and (not target.exists() or target.stat().st_size == 0):
                state.prefill_notes(target, w)
            elif target and target.exists():
                sess = state.current_session()
                if (sess and read_sync_turns(target) is not None
                        and sess.stat().st_mtime > target.stat().st_mtime):
                    state.append_new_turns(target)
            if target:
                open_cmd = "xdg-open" if state.open_pref == "auto" else state.open_pref
                try:
                    subprocess.Popen([open_cmd, str(target)])
                    flash_msg = f"  Opened via {open_cmd}: {target.name}"
                except FileNotFoundError:
                    flash_msg = f"  {open_cmd}: nicht gefunden."
            else:
                flash_msg = "  Keine Session ausgewählt."
            flash_timer = 30

        elif key == ord("u"):
            # [u] Aktuelle Notiz mit neuen Turns aus der JSONL aktualisieren
            target = state.notes_path()
            if target and target.exists() and target.stat().st_size > 0:
                flash_msg = state.append_new_turns(target)
                state._notes_text_cache.clear()
                state.refresh_notes(w)
                state.notes_scroll = len(state.notes_lines)   # ans Ende scrollen
            elif target and (not target.exists() or target.stat().st_size == 0):
                flash_msg = "  Noch keine Notiz — [E] zum Erstellen oder [U] für Batch-Update."
            else:
                flash_msg = "  Keine Session ausgewählt."
            flash_timer = 40

        elif key == ord("U"):
            # [U] Batch-Update: alle Notizen im aktuellen Projekt aktualisieren/anlegen
            flash_msg = state.update_all_notes(w)
            state.refresh_notes(w)
            flash_timer = 60

        elif key in (ord("s"), ord("S")):
            flash_msg = state.refresh()
            state.view_mode = "both"
            state.focus = "threads"
            state.preview_reader(w)
            flash_timer = 30

        elif key in (ord("a"), ord("A")):
            # Start Claude Code with --resume <uuid> — CWD from session metadata.
            # Voraussetzung: Live-JSONL muss in ~/.claude/projects/<proj>/ existieren.
            # Fehlt sie (nur Archiv vorhanden) → Hinweis auf [L] Lend.
            path = state.current_session()
            if path:
                uuid = path.stem
                if path.suffix == ".md":
                    live_jsonl = note_project(path) / f"{uuid}.jsonl"
                else:
                    live_jsonl = path
                if not live_jsonl.exists():
                    if is_archived(path):
                        flash_msg = "  Nur im Archiv — erst [L] Lend drücken, dann [a] starten."
                    else:
                        flash_msg = "  Verwaiste Notiz — weder Live noch Archiv, kein Resume möglich."
                    flash_timer = 40
                    continue
                cwd = get_session_cwd(live_jsonl)
                curses.endwin()
                subprocess.run(["claude", "--resume", uuid], cwd=cwd)
                stdscr.clear()
                stdscr.refresh()
                state.force_redraw = True
                flash_msg = f"  Agent done: {uuid[:8]}…"
                flash_timer = 30

        elif key == ord("L"):
            # [L] Lend — archivierte Session + Notiz zurück ins Live-Verzeichnis kopieren.
            # Setzt JSONL-mtime auf jetzt, damit Claude Codes Cleanup-Zähler resettet.
            # v1.26: zieht zusätzlich die zugehörige <uuid>.md aus dem Archiv,
            #        falls vorhanden — Kronjuwel mit zurück.
            path = state.current_session()
            if not path:
                flash_msg = "  Keine Session ausgewählt."
            else:
                if path.suffix == ".md":
                    target_proj = note_project(path)
                else:
                    target_proj = state.current_proj_for_session(path)
                arch = archive_path(target_proj.name, path.stem)
                if not arch.exists():
                    flash_msg = "  Nicht im Archiv — nichts zum Ausleihen."
                else:
                    try:
                        dest = restore_session(arch, target_proj)
                        note_lent = False
                        arch_note = archived_note_path(target_proj.name, path.stem)
                        if arch_note.exists():
                            mem_dir = target_proj / "memory"
                            mem_dir.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(arch_note, mem_dir / arch_note.name)
                            note_lent = True
                        state._sessions_cache.clear()
                        state._title_cache.pop(path, None)
                        state._tokens_cache.pop(path, None)
                        state._notes_text_cache.pop(path, None)
                        suffix = " + Notiz" if note_lent else ""
                        flash_msg = f"  Ausgeliehen{suffix}: {dest.name[:32]}… · mtime refresht"
                    except OSError as e:
                        flash_msg = f"  Fehler beim Ausleihen: {e}"
            flash_timer = 50

        elif key == ord("/"):
            state.search_active = True
            state.search_query = ""
            state.thread_idx = 0
            state.thread_scroll = 0
            state.focus = "threads"

        elif key == ord("#"):
            # [#] Tags setzen für aktuelle Session
            path = state.current_session()
            if path:
                current_tags = ", ".join(state.session_tags(path))
                new_tags = input_dialog(stdscr, "Tags", "Tags (komma-getrennt, z.B.: hvd, bugfix):",
                                        prefill=current_tags)
                state.force_redraw = True
                if new_tags is not None:
                    flash_msg = "  " + state.tag_current(new_tags)
                    flash_timer = 40

        # ── Projekte-Panel ────────────────────────────────────────────────────
        elif focus == "projects":
            if key in (curses.KEY_UP, ord("k")):
                if state.proj_idx > 0:
                    state.proj_idx -= 1
                    state.thread_idx = 0
                    state.thread_scroll = 0
                    state.search_query = ""
                    state._notes_text_cache.clear()
                    state._tags_cache.clear()
            elif key in (curses.KEY_DOWN, ord("j")):
                if state.proj_idx < len(state.projects) - 1:
                    state.proj_idx += 1
                    state.thread_idx = 0
                    state.thread_scroll = 0
                    state.search_query = ""
                    state._notes_text_cache.clear()
                    state._tags_cache.clear()
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                state.focus = "threads"

        # ── Thread-Panel ──────────────────────────────────────────────────────
        elif focus == "threads":
            sessions = state.filtered_sessions()
            moved = False
            if key in (curses.KEY_UP, ord("k")):
                if state.thread_idx > 0:
                    state.thread_idx -= 1
                    moved = True
            elif key in (curses.KEY_DOWN, ord("j")):
                if state.thread_idx < len(sessions) - 1:
                    state.thread_idx += 1
                    moved = True
            elif key == curses.KEY_HOME:
                state.thread_idx = 0
                moved = True
            elif key == curses.KEY_END:
                state.thread_idx = max(0, len(sessions) - 1)
                moved = True
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                state.open_reader(w)
            elif key == curses.KEY_LEFT:
                state.focus = "projects"
            # Auto-Preview: Reader-Inhalt bei Navigation aktualisieren
            if moved and state.reader_lines is not None:
                # Auto-swap zuerst setzen — preview_reader braucht korrektes swapped für Zeilenbreite
                if state.view_mode == "both":
                    np = state.notes_path()
                    has_note = np is not None and np.exists() and np.stat().st_size > 0
                    state.swapped = has_note
                state.preview_reader(w)

        # ── Reader ────────────────────────────────────────────────────────────
        elif focus == "reader":
            lines = state.reader_lines
            visible = reader_h - 2
            if key in (curses.KEY_UP, ord("k")):
                state.reader_scroll = max(0, state.reader_scroll - 1)
            elif key in (curses.KEY_DOWN, ord("j"), ord(" ")):
                state.reader_scroll = min(max(0, len(lines) - visible), state.reader_scroll + 1)
            elif key == curses.KEY_PPAGE:
                state.reader_scroll = max(0, state.reader_scroll - visible)
            elif key == curses.KEY_NPAGE:
                state.reader_scroll = min(max(0, len(lines) - visible), state.reader_scroll + visible)
            elif key == curses.KEY_HOME:
                state.reader_scroll = 0
            elif key == curses.KEY_END:
                state.reader_scroll = max(0, len(lines) - visible)
            elif key == curses.KEY_LEFT:
                state.focus = "threads"
            elif key == curses.KEY_RIGHT:
                state.focus = "notes"

        # ── Notizen-Panel ─────────────────────────────────────────────────────
        elif focus == "notes":
            lines = state.notes_lines
            visible = reader_h - 2
            if key in (curses.KEY_UP, ord("k")):
                state.notes_scroll = max(0, state.notes_scroll - 1)
            elif key in (curses.KEY_DOWN, ord("j"), ord(" ")):
                state.notes_scroll = min(max(0, len(lines) - visible), state.notes_scroll + 1)
            elif key == curses.KEY_PPAGE:
                state.notes_scroll = max(0, state.notes_scroll - visible)
            elif key == curses.KEY_NPAGE:
                state.notes_scroll = min(max(0, len(lines) - visible), state.notes_scroll + visible)
            elif key == curses.KEY_HOME:
                state.notes_scroll = 0
            elif key == curses.KEY_END:
                state.notes_scroll = max(0, len(lines) - visible)
            elif key == curses.KEY_LEFT:
                state.focus = "reader"


_EDITOR_PRESETS: list[str] = ["auto", "msedit", "nano"]
_OPEN_PRESETS:   list[str] = ["auto", "typora"]

LANGS: list[str] = ["de", "en", "fr", "ja", "es"]

HELP_TEXTS: dict[str, str] = {
    "de": """
XED /TUI v1 — Vollständige Keybinding-Referenz
=============================================
Starten: python xed_tui_v1.py

Navigation
  ↑↓ / j k         Zeile hoch/runter
  J K              5 Zeilen hoch/runter
  PgUp / PgDn      Seite hoch/runter
  Home / End       Erste / Letzte Zeile
  Tab / F6         Panel wechseln: Projekte ↔ Sessions ↔ Reader ↔ Notizen
  ← →              Zwischen Reader und Notizen wechseln
  Enter            Session öffnen (Reader)

Layout
  0                Top-Panel ausblenden
  1–9              Top-Panel-Höhe n×5 Zeilen (Standard: 4 = 20 Zeilen)
  f / F            Full — nur Reader (Vollbild)
  n / N            Nur Notizen (Vollbild)
  m / M            Beide Panels — oder Seiten tauschen

Session-Management
  s / S            Sessions neu laden + Fokus auf Sessions-Panel (setzt Filter zurück)
  t / T            Titel setzen (persistiert in ~/.xed/tui/state/<proj>/titles.json + JSONL)
  d / D            Session löschen (Bestätigung: "delete" tippen)
  a / A            Claude Code mit --resume <uuid> starten (CWD aus Session-Metadaten)
  L                Lend — archivierte Session + Notiz zurück ins ~/.claude/ (v1.26)
                   (Bibliothek → Live; JSONL-mtime wird aktualisiert → Cleanup-Reset)
  r / R            /resume <uuid> in Zwischenablage (für laufendes Claude Code)

Suche & Tags
  /                Suche — Live-Filter nach Titel + Notizen
                   Tipp: #tag tippen filtert nach Tag (z.B. /#hvd)
  #                Tags setzen für aktuelle Session (komma-getrennt)

Notizen
  e / E            Notiz im Editor öffnen ($EDITOR oder nano)
                   → Neue Notiz: Transcript als Prefill + .sync anlegen
                   → Bestehende Notiz: neue Turns automatisch anhängen (wenn .sync vorhanden)
  o / O            Notiz in Standard-App öffnen (xdg-open, z.B. Typora/Obsidian)
  u                Notiz manuell mit neuen Turns aktualisieren (ohne Editor zu öffnen)
  U                Batch: ALLE Notizen im Projekt aktualisieren (+ fehlende anlegen)
  c / C            Notiz in Zwischenablage (wl-copy / xclip / xsel)

Sonstiges
  ? / h / H        Hilfe-Overlay
  Ctrl+E           Einstellungen (Editor für [E], App für [O])
  q / Q            Sofort beenden
  ESC              Beenden mit Bestätigung

Datei-Struktur (v1.26)
  ~/.claude/projects/<proj>/              Claudes Hoheit
  ├── <uuid>.jsonl          Session-Transcript (Claudes Datei, read-only für XED)
  └── memory/
      ├── <uuid>.md         Notiz-Datei (XED schreibt, manuell editierbar)
      └── MEMORY.md         Auto-Memory-Index (Claudes Datei)
  ~/.xed/tui/                             XED-eigenes Territorium
  ├── archive/<proj>/       Bibliothek: <uuid>.jsonl (Bände) + <uuid>.md (Katalogkarten)
  └── state/                XED-Sidecars (ab v1.26, vorher im memory/)
      ├── continue.json     TUI-Wiederaufnahme nach Neustart
      └── <proj>/
          ├── titles.json   Custom-Titel      {uuid: "Mein Titel"}
          ├── tags.json     Tags pro Session  {uuid: ["hvd", "bugfix"]}
          └── <uuid>.sync   Sync-Status (synchronisierte Turns)

XED /TUI @ Collective Context
""",
    "en": """
XED /TUI v1 — Complete Keybinding Reference
==========================================
Start: python xed_tui_v1.py

Navigation
  ↑↓ / j k         Line up/down
  J K              5 lines up/down
  PgUp / PgDn      Page up/down
  Home / End       First / Last line
  Tab / F6         Switch panel: Projects ↔ Sessions ↔ Reader ↔ Notes
  ← →              Switch between Reader and Notes
  Enter            Open session (Reader)

Layout
  0                Hide top panel
  1–9              Top panel height n×5 lines (default: 4 = 20 lines)
  f / F            Full — Reader only (fullscreen)
  n / N            Notes only (fullscreen)
  m / M            Both panels — or swap sides

Session Management
  s / S            Reload sessions + focus Sessions panel (resets filter)
  t / T            Set title (persists in ~/.xed/tui/state/<proj>/titles.json + JSONL)
  d / D            Delete session (confirm by typing "delete")
  a / A            Start Claude Code with --resume <uuid> (CWD from session metadata)
  L                Lend — restore archived session + note back into ~/.claude/ (v1.26)
                   (library → live; JSONL mtime refreshed → Claude Code cleanup reset)
  r / R            /resume <uuid> to clipboard (for running Claude Code)

Search & Tags
  /                Search — live filter by title + notes
                   Tip: type #tag to filter by tag (e.g. /#hvd)
  #                Set tags for current session (comma-separated)

Notes
  e / E            Open note in editor ($EDITOR or nano)
                   → New note: transcript as prefill + create .sync
                   → Existing note: auto-append new turns (if .sync exists)
  o / O            Open note in default app (xdg-open, e.g. Typora/Obsidian)
  u                Update note manually with new turns (without opening editor)
  U                Batch: update ALL notes in project (+ create missing ones)
  c / C            Copy note to clipboard (wl-copy / xclip / xsel)

Other
  ? / h / H        Help overlay
  Ctrl+E           Settings (editor for [E], app for [O])
  q / Q            Quit immediately
  ESC              Quit with confirmation

File Structure (v1.26)
  ~/.claude/projects/<proj>/              Claude's territory
  ├── <uuid>.jsonl          Session transcript (Claude's file, read-only for XED)
  └── memory/
      ├── <uuid>.md         Note file (XED writes; manually editable)
      └── MEMORY.md         Auto-memory index (Claude's file)
  ~/.xed/tui/                             XED's own territory
  ├── archive/<proj>/       Library: <uuid>.jsonl (volumes) + <uuid>.md (catalog cards)
  └── state/                XED sidecars (since v1.26, formerly in memory/)
      ├── continue.json     TUI restore state
      └── <proj>/
          ├── titles.json   Custom titles     {uuid: "My Title"}
          ├── tags.json     Tags per session  {uuid: ["hvd", "bugfix"]}
          └── <uuid>.sync   Sync status (synced turns count)

XED /TUI @ Collective Context
""",
    "fr": """
XED /TUI v1 — Référence complète des raccourcis
===============================================
Démarrer: python xed_tui_v1.py

Navigation
  ↑↓ / j k         Ligne haut/bas
  J K              5 lignes haut/bas
  PgUp / PgDn      Page haut/bas
  Home / End       Première / Dernière ligne
  Tab / F6         Changer panneau: Projets ↔ Sessions ↔ Lecteur ↔ Notes
  ← →              Basculer entre Lecteur et Notes
  Enter            Ouvrir la session (Lecteur)

Disposition
  0                Masquer le panneau supérieur
  1–9              Hauteur panneau sup. n×5 lignes (défaut: 4 = 20 lignes)
  f / F            Plein écran — Lecteur uniquement
  n / N            Notes uniquement (plein écran)
  m / M            Les deux panneaux — ou inverser les côtés

Gestion des sessions
  s / S            Recharger sessions + focus panneau Sessions (réinitialise filtre)
  t / T            Définir titre (persistant dans ~/.xed/tui/state/<proj>/titles.json + JSONL)
  d / D            Supprimer session (confirmer en tapant "delete")
  a / A            Lancer Claude Code avec --resume <uuid> (CWD des métadonnées)
  L                Lend — restaurer session archivée + note dans ~/.claude/ (v1.26)
                   (bibliothèque → live ; mtime JSONL actualisé → reset du nettoyage)
  r / R            /resume <uuid> vers presse-papiers (pour Claude Code en cours)

Recherche & Étiquettes
  /                Recherche — filtre en direct par titre + notes
                   Conseil: taper #tag filtre par étiquette (ex. /#hvd)
  #                Définir étiquettes pour la session actuelle (séparées par virgule)

Notes
  e / E            Ouvrir note dans l'éditeur ($EDITOR ou nano)
                   → Nouvelle note: transcript comme préfill + créer .sync
                   → Note existante: ajouter nouveaux tours automatiquement
  o / O            Ouvrir note dans l'app par défaut (xdg-open, ex. Typora/Obsidian)
  u                Mettre à jour note manuellement (sans ouvrir l'éditeur)
  U                Lot : mettre à jour TOUTES les notes (+ créer les manquantes)
  c / C            Copier note dans presse-papiers (wl-copy / xclip / xsel)

Autre
  ? / h / H        Aide (cette fenêtre)
  Ctrl+E           Paramètres (éditeur pour [E], app pour [O])
  q / Q            Quitter immédiatement
  ESC              Quitter avec confirmation

Structure des fichiers (v1.26)
  ~/.claude/projects/<proj>/              Territoire Claude
  ├── <uuid>.jsonl          Transcript de session (fichier Claude, XED lit seulement)
  └── memory/
      ├── <uuid>.md         Fichier note (écrit par XED, modifiable manuellement)
      └── MEMORY.md         Index auto-memory (fichier Claude)
  ~/.xed/tui/                             Territoire XED
  ├── archive/<proj>/       Bibliothèque: <uuid>.jsonl (volumes) + <uuid>.md (catalogue)
  └── state/                Sidecars XED (depuis v1.26, avant dans memory/)
      ├── continue.json     État de reprise du TUI
      └── <proj>/
          ├── titles.json   Titres personnalisés    {uuid: "Mon titre"}
          ├── tags.json     Étiquettes par session  {uuid: ["hvd", "bugfix"]}
          └── <uuid>.sync   Statut sync (tours synchronisés)

XED /TUI @ Collective Context
""",
    "ja": """
XED /TUI v1 — キーバインド完全リファレンス
==========================================
起動: python xed_tui_v1.py

ナビゲーション
  ↑↓ / j k         1行上下
  J K              5行上下
  PgUp / PgDn      ページ上下
  Home / End       先頭 / 末尾行
  Tab / F6         パネル切替: プロジェクト ↔ セッション ↔ リーダー ↔ ノート
  ← →              リーダーとノートの切替
  Enter            セッションを開く (リーダー)

レイアウト
  0                上部パネルを非表示
  1–9              上部パネル高さ n×5行 (デフォルト: 4 = 20行)
  f / F            フルスクリーン — リーダーのみ
  n / N            ノートのみ (フルスクリーン)
  m / M            両パネル — または左右入替

セッション管理
  s / S            セッション再読込 + セッションパネルにフォーカス
  t / T            タイトル設定 (~/.xed/tui/state/<proj>/titles.json + JSONL に保存)
  d / D            セッション削除 ("delete" と入力して確認)
  a / A            Claude Code を --resume <uuid> で起動
  L                Lend — アーカイブ済みセッション + ノートを ~/.claude/ に復元 (v1.26)
                   (ライブラリ → ライブ; JSONL mtime 更新 → クリーンアップリセット)
  r / R            /resume <uuid> をクリップボードにコピー

検索 & タグ
  /                検索 — タイトル+ノートのライブフィルタ
                   ヒント: #タグ でタグ検索 (例: /#hvd)
  #                現在のセッションにタグを設定 (カンマ区切り)

ノート
  e / E            エディタでノートを開く ($EDITOR または nano)
                   → 新規ノート: トランスクリプトをプリフィル + .sync 作成
                   → 既存ノート: 新しいターンを自動追記 (.sync がある場合)
  o / O            標準アプリでノートを開く (xdg-open、例: Typora/Obsidian)
  u                エディタを開かずにノートを手動更新
  U                一括：プロジェクト内のすべてのノートを更新（無いものは作成）
  c / C            ノートをクリップボードにコピー (wl-copy / xclip / xsel)

その他
  ? / h / H        ヘルプ (このウィンドウ)
  Ctrl+E           設定 ([E] のエディタ、[O] のアプリ)
  q / Q            即時終了
  ESC              確認して終了

ファイル構成 (v1.26)
  ~/.claude/projects/<proj>/              Claude の領域
  ├── <uuid>.jsonl          セッショントランスクリプト (Claude のファイル、XED は読取専用)
  └── memory/
      ├── <uuid>.md         ノートファイル (XED が書込、手動編集可)
      └── MEMORY.md         Auto-memory インデックス (Claude のファイル)
  ~/.xed/tui/                             XED の領域
  ├── archive/<proj>/       ライブラリ: <uuid>.jsonl (巻) + <uuid>.md (目録カード)
  └── state/                XED サイドカー (v1.26 以降、以前は memory/)
      ├── continue.json     TUI 再開状態
      └── <proj>/
          ├── titles.json   カスタムタイトル  {uuid: "マイタイトル"}
          ├── tags.json     セッションのタグ  {uuid: ["hvd", "bugfix"]}
          └── <uuid>.sync   同期状態 (同期済みターン数)

XED /TUI @ Collective Context
""",
    "es": """
XED /TUI v1 — Referencia completa de atajos
============================================
Iniciar: python xed_tui_v1.py

Navegación
  ↑↓ / j k         Línea arriba/abajo
  J K              5 líneas arriba/abajo
  PgUp / PgDn      Página arriba/abajo
  Home / End       Primera / Última línea
  Tab / F6         Cambiar panel: Proyectos ↔ Sesiones ↔ Lector ↔ Notas
  ← →              Alternar entre Lector y Notas
  Enter            Abrir sesión (Lector)

Disposición
  0                Ocultar panel superior
  1–9              Altura panel sup. n×5 líneas (defecto: 4 = 20 líneas)
  f / F            Pantalla completa — solo Lector
  n / N            Solo Notas (pantalla completa)
  m / M            Ambos paneles — o intercambiar lados

Gestión de sesiones
  s / S            Recargar sesiones + enfocar panel Sesiones (reinicia filtro)
  t / T            Establecer título (persiste en ~/.xed/tui/state/<proj>/titles.json + JSONL)
  d / D            Eliminar sesión (confirmar escribiendo "delete")
  a / A            Iniciar Claude Code con --resume <uuid> (CWD de metadatos)
  L                Lend — restaurar sesión archivada + nota en ~/.claude/ (v1.26)
                   (biblioteca → live; mtime JSONL actualizado → reset de limpieza)
  r / R            /resume <uuid> al portapapeles (para Claude Code en ejecución)

Búsqueda & Etiquetas
  /                Búsqueda — filtro en vivo por título + notas
                   Consejo: escribe #etiqueta para filtrar por tag (ej. /#hvd)
  #                Establecer etiquetas para la sesión actual (separadas por coma)

Notas
  e / E            Abrir nota en editor ($EDITOR o nano)
                   → Nueva nota: transcript como prefill + crear .sync
                   → Nota existente: añadir nuevos turnos automáticamente
  o / O            Abrir nota en app predeterminada (xdg-open, ej. Typora/Obsidian)
  u                Actualizar nota manualmente con nuevos turnos
  U                Lote: actualizar TODAS las notas del proyecto (+ crear las faltantes)
  c / C            Copiar nota al portapapeles (wl-copy / xclip / xsel)

Otros
  ? / h / H        Ayuda (esta ventana)
  Ctrl+E           Configuración (editor para [E], app para [O])
  q / Q            Salir inmediatamente
  ESC              Salir con confirmación

Estructura de archivos (v1.26)
  ~/.claude/projects/<proj>/              Territorio de Claude
  ├── <uuid>.jsonl          Transcript de sesión (archivo de Claude, XED solo lee)
  └── memory/
      ├── <uuid>.md         Archivo de nota (XED escribe, editable manualmente)
      └── MEMORY.md         Índice auto-memory (archivo de Claude)
  ~/.xed/tui/                             Territorio de XED
  ├── archive/<proj>/       Biblioteca: <uuid>.jsonl (volúmenes) + <uuid>.md (catálogo)
  └── state/                Sidecars XED (desde v1.26, antes en memory/)
      ├── continue.json     Estado de reanudación del TUI
      └── <proj>/
          ├── titles.json   Títulos personalizados {uuid: "Mi título"}
          ├── tags.json     Etiquetas por sesión  {uuid: ["hvd", "bugfix"]}
          └── <uuid>.sync   Estado sync (turnos sincronizados)

XED /TUI @ Collective Context
""",
}


def print_paged(text: str) -> None:
    """more-artiges Paging: pausiert nach je einer Bildschirmseite."""
    lines = text.splitlines()
    page_size = max(shutil.get_terminal_size().lines - 1, 5)
    if not _HAS_TERMIOS or not sys.stdin.isatty():
        # Windows fallback or non-TTY (CI, pipes): print all at once
        print(text)
        return
    i = 0
    while i < len(lines):
        for line in lines[i:i + page_size]:
            print(line)
        i += page_size
        if i >= len(lines):
            break
        print("\033[7m-- More -- (SPACE/ENTER weiter, q beenden)\033[m", end="", flush=True)
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print("\r\033[K", end="")  # Prompt-Zeile löschen
        if ch in ("q", "Q", "\x1b"):
            break


def run():
    args = sys.argv[1:]
    if args and args[0] in ("--help", "-h"):
        print_paged(HELP_TEXTS["de"])
        sys.exit(0)
    continue_data = load_continue_state() if ("--continue" in args or "-c" in args) else None
    if not CLAUDE_PROJECTS.exists():
        print(f"Verzeichnis nicht gefunden: {CLAUDE_PROJECTS}", file=sys.stderr)
        sys.exit(1)
    locale.setlocale(locale.LC_ALL, "")      # UTF-8 für curses (Umlaute, Sonderzeichen)
    os.environ.setdefault("ESCDELAY", "25")  # ESC ohne 1000ms ncurses-Wartezeit
    curses.wrapper(lambda s: main(s, continue_data))


if __name__ == "__main__":
    run()
