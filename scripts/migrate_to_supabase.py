"""
SQLite → Supabase(PostgreSQL) 데이터 마이그레이션 스크립트
"""
import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from pathlib import Path

SQLITE_PATH = Path(__file__).resolve().parents[1] / "data" / "reports.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL 환경변수가 없습니다.")
    sys.exit(1)

print(f"SQLite: {SQLITE_PATH}")
print("Supabase 연결 중...")

sqlite = sqlite3.connect(str(SQLITE_PATH))
sqlite.row_factory = sqlite3.Row

pg = psycopg2.connect(DATABASE_URL)
pg.autocommit = False
cur = pg.cursor()

# 기존 데이터 삭제
print("기존 데이터 삭제 중...")
cur.execute("DELETE FROM report_values")
cur.execute("DELETE FROM report_notes")
cur.execute("DELETE FROM report_imports")
pg.commit()

# report_imports 마이그레이션
print("report_imports 마이그레이션 중...")
rows = sqlite.execute("SELECT * FROM report_imports ORDER BY id").fetchall()
for row in rows:
    cur.execute("""
        INSERT INTO report_imports (id, source_file, company_name, representatives, biz_no, report_date, imported_at, industry, main_product)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (row["id"], row["source_file"], row["company_name"], row["representatives"],
          row["biz_no"], row["report_date"], row["imported_at"], row["industry"], row["main_product"]))
pg.commit()
print(f"  완료: {len(rows)}건")

# report_notes 마이그레이션
print("report_notes 마이그레이션 중...")
rows = sqlite.execute("SELECT * FROM report_notes ORDER BY id").fetchall()
batch = []
for row in rows:
    batch.append((row["id"], row["import_id"], row["row_no"], row["section"], row["line"]))
    if len(batch) >= 1000:
        psycopg2.extras.execute_values(cur,
            "INSERT INTO report_notes (id, import_id, row_no, section, line) VALUES %s", batch)
        pg.commit()
        batch = []
if batch:
    psycopg2.extras.execute_values(cur,
        "INSERT INTO report_notes (id, import_id, row_no, section, line) VALUES %s", batch)
    pg.commit()
print(f"  완료: {len(rows)}건")

# report_values 마이그레이션
print("report_values 마이그레이션 중...")
rows = sqlite.execute("SELECT * FROM report_values ORDER BY id").fetchall()
total = len(rows)
batch = []
count = 0
for row in rows:
    batch.append((row["id"], row["import_id"], row["row_no"], row["section"], row["unit"],
                  row["metric"], row["period"], row["submetric"], row["category"],
                  row["value_raw"], row["value_num"]))
    if len(batch) >= 2000:
        psycopg2.extras.execute_values(cur, """
            INSERT INTO report_values (id, import_id, row_no, section, unit, metric, period, submetric, category, value_raw, value_num)
            VALUES %s""", batch)
        pg.commit()
        count += len(batch)
        print(f"  {count}/{total}...")
        batch = []
if batch:
    psycopg2.extras.execute_values(cur, """
        INSERT INTO report_values (id, import_id, row_no, section, unit, metric, period, submetric, category, value_raw, value_num)
        VALUES %s""", batch)
    pg.commit()
    count += len(batch)
print(f"  완료: {count}건")

# 시퀀스 동기화
print("시퀀스 동기화 중...")
for table in ["report_imports", "report_notes", "report_values"]:
    cur.execute(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}))")
pg.commit()

sqlite.close()
pg.close()
print("\n마이그레이션 완료!")
