"""Stage [1b] v3 — Extraction with table structure preservation.

CHANGELOG
=========
v3 (2026-07-12) — UNRULED TABLE SUPPORT.
    v2 detected tables via ruling lines only (pdfplumber's default
    `lines` strategy). Measured on the real corpus:

      * Interim results  -> 5 tables, 126 rows, 0 orphans.  PASS (ruled tables)
      * Earnings release -> 0 tables.                       FAIL (unruled)
      * Annual report    -> 5-year summary missed.          FAIL (unruled)

    Root cause: many financial tables are WHITESPACE-ALIGNED, not ruled. No
    grid lines exist, so `find_tables()` returns nothing and the content falls
    through to the prose path, where it is flattened into an unlabelled
    digit-wall -- the exact v1 defect, reintroduced by a different route.

    Fix: try the `lines` strategy first (precise, few false positives); if it
    finds nothing on a page that LOOKS tabular, retry with the `text` strategy,
    which infers columns from whitespace gutters.

    Also v3 — STRUCTURAL HEADER DETECTION (`find_header_row`).
    The `text` strategy pulls in surrounding title lines and blank spacers, so
    the header row is NOT reliably row 0. Blindly taking row 0 produced:

        Summarised income statement | million): 3,566,206      <-- garbage

    A first attempt keyed off "headers are non-numeric" -- WRONG, and instructive:
    in financial tables the header row is often YEARS ("2025 2024 2023"), i.e.
    entirely numeric. The heuristic failed on the very document class it exists
    to serve.

    The working signal is STRUCTURAL: financial tables leave the stub cell blank
    ('' | 2025 | 2024 | ...) while every data row carries a label in column 0.

KNOWN LIMITATION (documented, detected, not silently corrupted)
--------------------------------------------------------------
Heavily designed marketing layouts -- infographic panels with rotated or
curved text -- are extracted with character-level garbling ("UGX" -> "XGU",
"contributed" -> "contribu ... ted"). This is a glyph-ordering problem in the
source layout, not a table problem, and is OUT OF SCOPE for v1. The
verification harness DETECTS and FLAGS these rather than passing them
silently (see verify_extraction.py GATE 3).

DEPENDENCIES
------------
pdfplumber only. No new dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None


# --- Tunables (named, never magic numbers) -----------------------------------

ROW_LABEL_FALLBACK = "Item"

#: Minimum columns for a detected "table" to be treated as real data.
MIN_TABLE_COLS = 2

#: Minimum data rows (excluding header).
MIN_TABLE_ROWS = 1

#: Fraction of cells that must be non-empty for a detection to be a real table
#: rather than layout scaffolding.
MIN_FILL_RATIO = 0.4

#: A page is "probably tabular" (worth retrying with the text strategy) if this
#: many of its tokens are numeric. Tuned to admit financial statements without
#: dragging in ordinary prose that merely cites a few figures.
TABULAR_DIGIT_DENSITY = 0.18

#: Table settings. `lines` is tried first: it is precise and rarely produces
#: false positives. `text` is the fallback for whitespace-aligned tables.
LINES_STRATEGY = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
TEXT_STRATEGY = {"vertical_strategy": "text", "horizontal_strategy": "text"}


@dataclass
class Block:
    """A unit of extracted content."""

    kind: str  # "table" | "prose"
    text: str  # the embeddable representation
    page: int
    top: float
    display: str = ""
    n_rows: int = 0
    n_cols: int = 0
    strategy: str = ""  # "lines" | "text" — which detector found this table


def _clean_cell(v: object) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def _numeric_token(tok: str) -> bool:
    """True only for tokens containing at least one DIGIT.

    A bare '.' is not a number. (This exact bug caused the v2.0 harness to
    misfire on tables-of-contents.)
    """
    if not any(c.isdigit() for c in tok):
        return False
    return bool(re.fullmatch(r"[\d,.()%\-+]+", tok))


def page_digit_density(page) -> float:
    """Share of a page's tokens that are numeric literals."""
    text = page.extract_text() or ""
    toks = text.split()
    if not toks:
        return 0.0
    return sum(_numeric_token(t) for t in toks) / len(toks)


def _is_data_value(cell: str) -> bool:
    """True if the cell looks like a DATA VALUE (a pure number with separators).

    Deliberately NOT "contains a digit": header cells are frequently numeric
    ('2025', 'June 2024', 'H1 2024'). The distinction is between a *value*
    (1,522,676) and a *period label* (June 2024) — the latter carries letters or
    is a bare year in a header stack.
    """
    if not cell:
        return False
    if not any(ch.isdigit() for ch in cell):
        return False
    return bool(re.fullmatch(r"[\d,.()%\-+\s]+", cell))


def find_header_span(rows: list[list[str]]) -> tuple[int | None, int | None]:
    """Locate the header STACK. Headers may span SEVERAL rows.

    WHY THIS EXISTS (v3.1)
    ----------------------
    Statutory financial statements stack their headers three deep:

        (blank)    June 2024   June 2023   Dec 2023     <- period  (disambiguating)
        (blank)    Reviewed    Reviewed    Audited      <- audit status
        (blank)    Shs '000    Shs '000    Shs '000     <- units

    A single-row header picker takes ONE of these. On the real MTN statements it
    took the UNITS row, producing:

        Property, plant and equipment | Shs '000: 1,200,858,421 | Shs '000: 1,031,959,769

    Three columns, three IDENTICAL headers. Which is June 2024? Unanswerable —
    a milder form of the original v1 defect: the value carries *a* label, but not
    the *disambiguating* one. Users ask about the PERIOD.

    SIGNAL: a header row has an empty stub cell AND its value cells are not data
    values. A data row has a labelled stub and numeric values. The stack is the
    maximal run of header rows before the first data row.

    FALLBACK: first row with >= 3 filled cells — ruled tables usually DO label
    their stub ("Ush million"), so no blank-stub row exists.
    """
    start = None
    for i, r in enumerate(rows):
        later = [c for c in r[1:] if c]
        if not later:
            continue
        data_like = sum(_is_data_value(c) for c in later) / len(later)
        is_header = (not r[0]) and data_like < 0.5

        if is_header:
            if start is None:
                start = i
        elif start is not None:
            return start, i  # first data row ends the stack

    if start is not None:
        return start, len(rows)

    for i, r in enumerate(rows):
        if sum(1 for c in r if c) >= 3:
            return i, i + 1
    return None, None


def merge_header_stack(rows: list[list[str]], start: int, end: int) -> list[str]:
    """Flatten a multi-row header stack into composite column names.

        ['June 2024', 'Reviewed', "Shs '000"]  ->  "June 2024 Reviewed Shs '000"

    The period leads because that is what disambiguates the column and what
    users' questions key on. Units and audit status are retained: they are
    genuine context the LLM can cite, and they cost only a few tokens.
    """
    width = max((len(rows[r]) for r in range(start, end)), default=0)
    headers: list[str] = []
    for ci in range(width):
        parts = [
            rows[r][ci].strip()
            for r in range(start, end)
            if ci < len(rows[r]) and rows[r][ci].strip()
        ]
        headers.append(" ".join(parts))
    return headers


def _is_real_table(rows: list[list[str]]) -> bool:
    """Reject layout scaffolding masquerading as a table."""
    if len(rows) < MIN_TABLE_ROWS + 1:
        return False
    if max((len(r) for r in rows), default=0) < MIN_TABLE_COLS:
        return False
    filled = sum(1 for r in rows for c in r if c)
    total = sum(len(r) for r in rows) or 1
    return (filled / total) >= MIN_FILL_RATIO


def serialise_table(rows: list[list[str]]) -> str:
    """Turn a table into header-carrying, self-describing rows.

    THE CORE FIX of the whole extraction rework.

    Input:
        [['', '2025', '2024'],
         ['Service revenue', '3,566,206', '3,143,587']]

    Output:
        Service revenue | 2025: 3,566,206 | 2024: 3,143,587

    Every number travels with BOTH its column name and its row name, in plain
    text, in the same chunk. The embedding encodes the association; a bare
    digit-wall does not. If the row is retrieved, the LLM READS the mapping
    instead of inventing it.

    Why not a Markdown pipe table? The header appears once, at the top — so any
    chunk holding only middle rows loses it the moment a table spans a chunk
    boundary, reintroducing the original defect. Row-serialisation makes every
    row independently self-contained, which is the property chunking needs.
    """
    start, end = find_header_span(rows)
    if start is None:
        return ""

    merged = merge_header_stack(rows, start, end)
    headers = []
    for i, h in enumerate(merged):
        h = h.strip()
        if not h:
            h = ROW_LABEL_FALLBACK if i == 0 else f"col{i}"
        headers.append(h)

    lines: list[str] = []
    for raw in rows[end:]:
        cells = [_clean_cell(c) for c in raw]
        if not any(cells):
            continue
        cells += [""] * (len(headers) - len(cells))

        row_label = cells[0] or ROW_LABEL_FALLBACK
        parts = [
            f"{headers[i]}: {cells[i]}"
            for i in range(1, len(headers))
            if cells[i]
        ]
        if parts:
            lines.append(f"{row_label} | " + " | ".join(parts))

    return "\n".join(lines)


def render_pipe_table(rows: list[list[str]]) -> str:
    """Human-readable form (for inspection only — never embedded)."""
    start, end = find_header_span(rows)
    if start is None:
        return ""
    headers = [h or f"col{i}" for i, h in enumerate(merge_header_stack(rows, start, end))]
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for raw in rows[end:]:
        cells = [_clean_cell(c) for c in raw]
        cells += [""] * (len(headers) - len(cells))
        if any(cells):
            out.append("| " + " | ".join(cells[: len(headers)]) + " |")
    return "\n".join(out)


def _extract_tables(page, settings: dict) -> list[tuple]:
    """Return [(bbox, rows)] for tables found with the given settings."""
    found = []
    for tbl in page.find_tables(table_settings=settings):
        rows = [[_clean_cell(c) for c in row] for row in tbl.extract()]
        rows = [r for r in rows if any(r)]  # drop spacer rows
        if _is_real_table(rows):
            found.append((tbl.bbox, rows))
    return found


def extract_page_blocks(page, page_no: int) -> list[Block]:
    """Extract one page: tables structured, prose de-duplicated.

    STRATEGY CASCADE:
      1. `lines` — precise, low false-positive rate. Handles ruled tables.
      2. `text`  — fallback for whitespace-aligned tables, tried ONLY when
         `lines` found nothing AND the page looks numeric. Gating on digit
         density matters: the text strategy is aggressive and will happily
         "find" a table in ordinary prose if allowed to run unconditionally.

    ORDER OF OPERATIONS: tables are located first and their regions are then
    EXCLUDED from the prose pass, so table numbers are never re-emitted as a
    loose digit-wall alongside their structured form.
    """
    blocks: list[Block] = []

    found = _extract_tables(page, LINES_STRATEGY)
    strategy = "lines"

    if not found and page_digit_density(page) >= TABULAR_DIGIT_DENSITY:
        found = _extract_tables(page, TEXT_STRATEGY)
        strategy = "text"

    table_bboxes = []
    for bbox, rows in found:
        body = serialise_table(rows)
        if not body.strip():
            continue
        table_bboxes.append(bbox)
        blocks.append(
            Block(
                kind="table",
                text=body,
                display=render_pipe_table(rows),
                page=page_no,
                top=bbox[1],
                n_rows=len(rows) - 1,
                n_cols=max((len(r) for r in rows), default=0),
                strategy=strategy,
            )
        )

    def _outside_tables(obj) -> bool:
        if obj.get("object_type") not in ("char", "textline", "word"):
            return True
        cx = (obj["x0"] + obj["x1"]) / 2
        cy = (obj["top"] + obj["bottom"]) / 2
        for x0, top, x1, bottom in table_bboxes:
            if x0 <= cx <= x1 and top <= cy <= bottom:
                return False
        return True

    try:
        src = page.filter(_outside_tables) if table_bboxes else page
        prose = src.extract_text(layout=False) or ""
    except Exception:
        # Degrade gracefully: better slightly duplicated prose than a lost page.
        prose = page.extract_text() or ""

    for para in re.split(r"\n\s*\n", prose):
        para = re.sub(r"[ \t]+", " ", para).strip()
        if len(para) >= 15:  # below this it is page furniture
            blocks.append(Block(kind="prose", text=para, page=page_no, top=0.0))

    blocks.sort(key=lambda b: (0 if b.kind == "table" else 1, b.top))
    return blocks


def extract(path: str | Path) -> list[Block]:
    """Extract a born-digital PDF into ordered, structure-preserving blocks."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is required for extraction")

    blocks: list[Block] = []
    with pdfplumber.open(Path(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            blocks.extend(extract_page_blocks(page, i))
    return blocks
