import argparse
import os
import re
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.reports.paths import DB_PATH, EXPORT_DIR, ensure_project_dirs


def sanitize_sheet_name(name: str, used: set) -> str:
    # Excel sheet name constraints: 31 chars max, and cannot contain: : \ / ? * [ ]
    s = name.strip()
    s = re.sub(r"[:\\\/\?\*\[\]]", "_", s)
    s = re.sub(r"\s+", " ", s)
    if not s:
        s = "Company"
    s = s[:31]
    base = s
    i = 2
    while s in used:
        suffix = f"_{i}"
        s = (base[: 31 - len(suffix)] + suffix)[:31]
        i += 1
    used.add(s)
    return s


def company_from_source_file(source_file: str) -> str:
    # Typical filename pattern:
    #   20260330_평화홀딩스(주)_new csv.csv
    #   20260330_(주)화인트로.csv
    base = os.path.basename(source_file)
    # Remove extension
    base = re.sub(r"\.csv$|\.CSV$|\.xlsx$|\.XLSX$", "", base)
    # Remove leading date prefix (8 digits + underscore)
    base = re.sub(r"^\d{8}_", "", base)
    # Remove trailing markers
    base = re.sub(r"(_new csv|_csv|_new)", "", base, flags=re.IGNORECASE)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base:
        return "UnknownCompany"
    return base


def fetch_values(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT
      rv.import_id,
      ri.source_file,
      rv.row_no,
      rv.section,
      rv.unit,
      rv.metric,
      rv.period,
      rv.submetric,
      rv.category,
      rv.value_raw,
      rv.value_num
    FROM report_values rv
    JOIN report_imports ri ON ri.id = rv.import_id
    ORDER BY rv.import_id, rv.section, rv.metric, rv.period, rv.submetric, rv.category, rv.id
    """
    return pd.read_sql_query(q, conn)


def fetch_notes(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT
      rn.import_id,
      ri.source_file,
      rn.row_no,
      rn.section,
      rn.line
    FROM report_notes rn
    JOIN report_imports ri ON ri.id = rn.import_id
    ORDER BY rn.import_id, rn.section, rn.row_no, rn.id
    """
    return pd.read_sql_query(q, conn)


def export_excel(db_path: str, out_path: str, include_notes: bool) -> None:
    conn = sqlite3.connect(db_path)
    try:
        values_df = fetch_values(conn)
        if include_notes:
            notes_df = fetch_notes(conn)
        else:
            notes_df = pd.DataFrame(columns=["import_id", "source_file", "row_no", "section", "line"])

        # Derive company display name from source_file for grouping.
        values_df["company_name_display"] = values_df["source_file"].map(company_from_source_file)
        if include_notes:
            notes_df["company_name_display"] = notes_df["source_file"].map(company_from_source_file)

        used_sheet_names: set = set()
        # Using ExcelWriter with openpyxl engine.
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for company in sorted(values_df["company_name_display"].dropna().unique()):
                sheet_name = sanitize_sheet_name(company, used_sheet_names)
                df = values_df[values_df["company_name_display"] == company].copy()
                # Remove helper column from output.
                df = df.drop(columns=["company_name_display"])
                df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

                if include_notes and not notes_df.empty:
                    ndf = notes_df[notes_df["company_name_display"] == company].copy()
                    if not ndf.empty:
                        ndf = ndf.drop(columns=["company_name_display"])
                        # Put notes after values table.
                        start_row = len(df) + 3
                        ndf.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)

    finally:
        conn.close()


def main() -> int:
    ensure_project_dirs()
    default_out = os.path.join(EXPORT_DIR, "reports_by_company.xlsx")
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH, help=f"reports.db path (default: {DB_PATH})")
    parser.add_argument("--out", default=default_out, help=f"Output xlsx (default: {default_out})")
    parser.add_argument("--include-notes", action="store_true", help="Also export report_notes into each company sheet")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    out_path = os.path.abspath(args.out)

    export_excel(db_path=db_path, out_path=out_path, include_notes=args.include_notes)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

