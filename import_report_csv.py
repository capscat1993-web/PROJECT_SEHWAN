import argparse
import csv
import datetime as dt
import os
import re
import sqlite3
import sys
from typing import Iterable, List, Optional, Sequence, Tuple


SCHEMA_SQL = r"""
CREATE TABLE report_imports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_file TEXT NOT NULL,
  company_name TEXT,
  representatives TEXT,
  biz_no TEXT,
  report_date TEXT,
  imported_at TEXT NOT NULL
);

CREATE TABLE report_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  import_id INTEGER NOT NULL REFERENCES report_imports(id) ON DELETE CASCADE,
  row_no INTEGER NOT NULL,
  section TEXT NOT NULL,
  line TEXT NOT NULL
);

CREATE TABLE report_values (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  import_id INTEGER NOT NULL REFERENCES report_imports(id) ON DELETE CASCADE,
  row_no INTEGER NOT NULL,
  section TEXT NOT NULL,
  unit TEXT,
  metric TEXT NOT NULL,
  period TEXT,
  submetric TEXT,
  category TEXT,
  value_raw TEXT,
  value_num REAL
);

CREATE INDEX idx_notes_import_section ON report_notes(import_id, section);
CREATE INDEX idx_values_import_metric ON report_values(import_id, metric);
CREATE INDEX idx_values_import_period ON report_values(import_id, period);
CREATE INDEX idx_values_import_section ON report_values(import_id, section);
"""


ENCODINGS = ["utf-8-sig", "cp949", "euc-kr"]
UNIT_RE = re.compile(r"^\(단위\s*:\s*(.*?)\s*\)\s*$")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def detect_encoding(csv_path: str) -> str:
    # Must follow: utf-8-sig -> cp949 -> euc-kr
    for enc in ENCODINGS:
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                f.read(4096)
            return enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Failed to decode CSV with encodings: {ENCODINGS}")


def read_csv_rows(csv_path: str, encoding: str) -> List[List[str]]:
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        # DART-export-like CSV. Commas separate columns, quotes wrap comma-containing numbers.
        reader = csv.reader(f, delimiter=",", quotechar='"')
        return [row for row in reader]


def extract_unit(cell: str) -> Optional[str]:
    m = UNIT_RE.match(cell.strip())
    if not m:
        return None
    return m.group(1).strip() or None


def normalize_submetric(s: str) -> Optional[str]:
    t = s.strip()
    if not t:
        return None
    # Handle slight variants by substring matching.
    if "금액" in t:
        return "금액"
    if "구성비" in t:
        return "구성비"
    # DART sometimes uses "증감" or "증(감)".
    if "증감" in t or ("증" in t and "감" in t):
        return "증감"
    return None


def parse_value_num(value_raw: Optional[str]) -> Optional[float]:
    if value_raw is None:
        return None
    s = value_raw.strip()
    if s == "":
        return None
    s_no_space = s.replace(" ", "")
    if s_no_space in {"-", "전기미입수", "전기미입수,"}:
        return None
    if s_no_space in {"∞"}:
        return None
    # Strip percent sign if present (numeric + unit column).
    if s_no_space.endswith("%"):
        s_no_space = s_no_space[:-1]
    # Handle parentheses negatives: (123) => -123
    if s_no_space.startswith("(") and s_no_space.endswith(")"):
        inner = s_no_space[1:-1]
        s_no_space = "-" + inner
    s_no_space = s_no_space.replace(",", "")
    try:
        return float(s_no_space)
    except ValueError:
        return None


def ensure_schema(conn: sqlite3.Connection) -> None:
    # Create tables/indexes exactly as required.
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;
        """
        + """
        CREATE TABLE IF NOT EXISTS report_imports (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_file TEXT NOT NULL,
          company_name TEXT,
          representatives TEXT,
          biz_no TEXT,
          report_date TEXT,
          imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          import_id INTEGER NOT NULL REFERENCES report_imports(id) ON DELETE CASCADE,
          row_no INTEGER NOT NULL,
          section TEXT NOT NULL,
          line TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_values (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          import_id INTEGER NOT NULL REFERENCES report_imports(id) ON DELETE CASCADE,
          row_no INTEGER NOT NULL,
          section TEXT NOT NULL,
          unit TEXT,
          metric TEXT NOT NULL,
          period TEXT,
          submetric TEXT,
          category TEXT,
          value_raw TEXT,
          value_num REAL
        );

        CREATE INDEX IF NOT EXISTS idx_notes_import_section ON report_notes(import_id, section);
        CREATE INDEX IF NOT EXISTS idx_values_import_metric ON report_values(import_id, metric);
        CREATE INDEX IF NOT EXISTS idx_values_import_period ON report_values(import_id, period);
        CREATE INDEX IF NOT EXISTS idx_values_import_section ON report_values(import_id, section);
        """
    )


def looks_like_integer(s: str) -> bool:
    t = s.strip()
    return bool(re.fullmatch(r"-?\d+", t))


def join_line(fields: Sequence[str]) -> str:
    return ",".join([f.strip() for f in fields if f is not None]).strip()


def detect_mode_header(
    fields: List[str],
    periods: List[str],
) -> Tuple[Optional[str], Optional[List[str]]]:
    # Category split header row: e.g. 당사,산업평균,당사,산업평균,...
    cats = [f.strip() for f in fields if f.strip() != ""]
    if cats and periods and len(cats) % len(periods) == 0:
        if all(c in {"당사", "산업평균"} for c in cats):
            return "category_split", cats

    # Submetric split header row: e.g. 금액,구성비,증감,금액,...
    subs = []
    for f in fields:
        n = normalize_submetric(f)
        if n is not None:
            subs.append(n)
    if subs and periods and len(subs) % len(periods) == 0:
        if all(x in {"금액", "구성비", "증감"} for x in subs):
            return "submetric_split", subs
    return None, None


def import_csv_to_db(csv_path: str, db_path: str) -> int:
    encoding = detect_encoding(csv_path)
    rows = read_csv_rows(csv_path, encoding=encoding)
    if len(rows) < 4:
        raise ValueError("CSV must have at least 4 rows for (company_name, representatives, biz_no, report_date)")

    # 1) First 4 lines: company_name, representatives, biz_no, report_date
    company_name = rows[0][0].strip() if rows[0] and rows[0][0] is not None else None
    representatives = rows[1][0].strip() if rows[1] and rows[1][0] is not None else None
    biz_no = rows[2][0].strip() if rows[2] and rows[2][0] is not None else None
    report_date = rows[3][0].strip() if rows[3] and rows[3][0] is not None else None

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        ensure_schema(conn)

        # Idempotent import: remove previous import for the same source_file.
        cur = conn.cursor()
        with conn:
            cur.execute("SELECT id FROM report_imports WHERE source_file = ?", (csv_path,))
            existing = [r[0] for r in cur.fetchall()]
            for import_id in existing:
                cur.execute("DELETE FROM report_imports WHERE id = ?", (import_id,))

            imported_at = utc_now_iso()
            cur.execute(
                """
                INSERT INTO report_imports (source_file, company_name, representatives, biz_no, report_date, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (csv_path, company_name, representatives, biz_no, report_date, imported_at),
            )
            import_id = cur.lastrowid

            # Parse remaining rows
            notes_to_insert: List[Tuple[int, int, str, str]] = []
            values_to_insert: List[
                Tuple[int, int, str, Optional[str], str, Optional[str], Optional[str], Optional[str], str, Optional[float]]
            ] = []

            current_section: Optional[str] = None
            current_unit: Optional[str] = None
            current_periods: Optional[List[str]] = None
            current_mode: Optional[str] = None  # basic | category_split | submetric_split
            mode_seq: Optional[List[str]] = None

            category_slots: int = 0
            submetric_slots: int = 0

            for row_no, raw_fields in enumerate(rows, start=1):
                if row_no <= 4:
                    continue

                # Normalize for classification; keep original-ish for value_raw.
                fields = [f.strip() for f in raw_fields]
                fields = [f for f in fields]  # preserve positions

                # Page number only: ignore
                if len(fields) == 1 and looks_like_integer(fields[0]):
                    continue

                # Section marker
                if len(fields) >= 2 and fields[0] == "■":
                    current_section = fields[1].strip()
                    current_unit = None
                    current_periods = None
                    current_mode = None
                    mode_seq = None
                    category_slots = 0
                    submetric_slots = 0
                    continue

                # Unit line: (단위 : ...)
                if len(fields) >= 1:
                    u = extract_unit(fields[0])
                    if u is not None:
                        current_unit = u
                        continue

                # Redundant header: company,|,biz_no (observed in sample)
                if (
                    len(fields) == 3
                    and fields[1] == "|"
                    and company_name is not None
                    and biz_no is not None
                    and fields[0] == company_name
                    and fields[2] == biz_no
                ):
                    continue

                # Empty or whitespace-only rows -> ignore
                if not any(f for f in fields):
                    continue

                # Data absence
                if any("데이터가 존재하지 않습니다." == f for f in fields):
                    notes_to_insert.append(
                        (import_id, row_no, current_section or "", join_line(fields))
                    )
                    continue

                # Period header
                if len(fields) >= 2 and fields[0] in {"과목명/결산년월", "계정명"}:
                    current_periods = [f for f in fields[1:] if f != ""]
                    current_mode = None
                    mode_seq = None
                    category_slots = 0
                    submetric_slots = 0
                    continue

                # Mode header (category/submetric) detection right after periods header
                if current_periods is not None and current_mode is None:
                    mode, seq = detect_mode_header(fields, current_periods)
                    if mode is not None and seq is not None:
                        current_mode = mode
                        mode_seq = seq
                        if mode == "category_split":
                            category_slots = len(seq) // len(current_periods)
                        elif mode == "submetric_split":
                            submetric_slots = len(seq) // len(current_periods)
                        continue

                # Value row parse attempt
                if current_section and current_periods is not None:
                    # Basic mode expects: metric + period values
                    if current_mode in (None, "basic"):
                        expected = 1 + len(current_periods)
                        if len(fields) == expected:
                            metric = fields[0]
                            values = fields[1:]
                            for idx, period in enumerate(current_periods):
                                v_raw = values[idx] if idx < len(values) else ""
                                values_to_insert.append(
                                    (
                                        import_id,
                                        row_no,
                                        current_section,
                                        current_unit,
                                        metric,
                                        period,
                                        None,
                                        None,
                                        v_raw,
                                        parse_value_num(v_raw),
                                    )
                                )
                            continue

                        # Some tables contain minor trailing empties; tolerate after trimming trailing empties.
                        trimmed = list(fields)
                        while trimmed and trimmed[-1] == "":
                            trimmed.pop()
                        if len(trimmed) == expected:
                            metric = trimmed[0]
                            values = trimmed[1:]
                            for idx, period in enumerate(current_periods):
                                v_raw = values[idx] if idx < len(values) else ""
                                values_to_insert.append(
                                    (
                                        import_id,
                                        row_no,
                                        current_section,
                                        current_unit,
                                        metric,
                                        period,
                                        None,
                                        None,
                                        v_raw,
                                        parse_value_num(v_raw),
                                    )
                                )
                            continue

                    # Category split mode expects: metric + (periods * category_slots)
                    if current_mode == "category_split" and mode_seq is not None:
                        expected = 1 + len(current_periods) * category_slots
                        if len(fields) == expected:
                            metric = fields[0]
                            for p_idx, period in enumerate(current_periods):
                                for j in range(category_slots):
                                    seq_idx = p_idx * category_slots + j
                                    category = mode_seq[seq_idx]
                                    col_idx = 1 + p_idx * category_slots + j
                                    v_raw = fields[col_idx]
                                    values_to_insert.append(
                                        (
                                            import_id,
                                            row_no,
                                            current_section,
                                            current_unit,
                                            metric,
                                            period,
                                            None,
                                            category,
                                            v_raw,
                                            parse_value_num(v_raw),
                                        )
                                    )
                            continue

                    # Submetric split mode expects: metric + (periods * submetric_slots)
                    if current_mode == "submetric_split" and mode_seq is not None:
                        expected = 1 + len(current_periods) * submetric_slots
                        if len(fields) == expected:
                            metric = fields[0]
                            for p_idx, period in enumerate(current_periods):
                                for j in range(submetric_slots):
                                    seq_idx = p_idx * submetric_slots + j
                                    submetric = mode_seq[seq_idx]
                                    col_idx = 1 + p_idx * submetric_slots + j
                                    v_raw = fields[col_idx]
                                    values_to_insert.append(
                                        (
                                            import_id,
                                            row_no,
                                            current_section,
                                            current_unit,
                                            metric,
                                            period,
                                            submetric,
                                            None,
                                            v_raw,
                                            parse_value_num(v_raw),
                                        )
                                    )
                            continue

                    # If we reached here, row is unparseable table/value row
                    notes_to_insert.append(
                        (import_id, row_no, current_section, join_line(raw_fields))
                    )
                    continue

                # Fallback note for unparsed rows when no table context exists.
                # This captures "설명 문장" and other non-tabular text.
                if any(f for f in fields):
                    notes_to_insert.append(
                        (import_id, row_no, current_section or "", join_line(raw_fields))
                    )

            cur.executemany(
                """
                INSERT INTO report_notes (import_id, row_no, section, line)
                VALUES (?, ?, ?, ?)
                """,
                notes_to_insert,
            )
            cur.executemany(
                """
                INSERT INTO report_values
                (import_id, row_no, section, unit, metric, period, submetric, category, value_raw, value_num)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values_to_insert,
            )

        return import_id
    finally:
        conn.close()


def run_validation(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()

        tables = ["report_imports", "report_notes", "report_values"]
        print("VALIDATION: table row counts")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            print(f"- {t}: {cnt}")

        print("\nVALIDATION: report_imports recent 1")
        q1 = "SELECT id, source_file, company_name, representatives, biz_no, report_date, imported_at FROM report_imports ORDER BY id DESC LIMIT 1"
        cur.execute(q1)
        rows = cur.fetchall()
        print(q1)
        for r in rows:
            print(r)

        print("\nVALIDATION: report_values sample (section='재무상태표')")
        q2 = """
        SELECT id, section, unit, metric, period, submetric, category, value_raw, value_num
        FROM report_values
        WHERE section = '재무상태표'
        ORDER BY id DESC
        LIMIT 5
        """
        cur.execute(q2)
        rows = cur.fetchall()
        print(q2.strip())
        for r in rows:
            print(r)

        print("\nVALIDATION: report_notes sample")
        q3 = """
        SELECT id, row_no, section, line
        FROM report_notes
        ORDER BY id DESC
        LIMIT 5
        """
        cur.execute(q3)
        rows = cur.fetchall()
        print(q3.strip())
        for r in rows:
            print(r)
    finally:
        conn.close()


def discover_csv_paths(default_csv_dir: str) -> List[str]:
    if not os.path.isdir(default_csv_dir):
        return []
    paths: List[str] = []
    for name in os.listdir(default_csv_dir):
        if name.lower().endswith(".csv"):
            paths.append(os.path.join(default_csv_dir, name))
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=None,
        help="Input CSV path (DART style). If omitted, imports all CSV files under ./csv.",
    )
    # Default DB path: project root / reports.db
    parser.add_argument("--db", default="reports.db", help="Output DB path (default: reports.db)")
    args = parser.parse_args(argv)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_paths: List[str] = []
    if args.csv_path is None:
        csv_dir = os.path.join(script_dir, "csv")
        csv_paths = discover_csv_paths(csv_dir)
        if not csv_paths:
            raise SystemExit("No CSV found under ./csv. Please pass csv_path explicitly.")
    else:
        csv_paths = [os.path.abspath(args.csv_path)]

    db_path = os.path.abspath(args.db)

    for csv_path in csv_paths:
        import_csv_to_db(os.path.abspath(csv_path), db_path)

    run_validation(db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

