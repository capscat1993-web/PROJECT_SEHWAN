"""
bizno.net에서 사업자번호로 업종/주요제품 정보를 수집해 DB에 저장하는 스크립트
"""
import sqlite3
import requests
import re
import sys
import time
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "reports.db"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_info(biz_no: str) -> dict:
    biz_clean = biz_no.replace("-", "")
    url = f"https://bizno.net/article/{biz_clean}"
    result = {"industry": "", "main_product": ""}
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        m_종 = re.search(r"종\s*목\s*\n\s*(.+)", text)
        m_제품 = re.search(r"주요제품\s*\n\s*(.+)", text)

        result["industry"] = m_종.group(1).strip() if m_종 else ""
        result["main_product"] = m_제품.group(1).strip() if m_제품 else ""
    except Exception:
        pass
    return result


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cols = [c["name"] for c in conn.execute("PRAGMA table_info(report_imports)").fetchall()]
    for col in ["industry", "main_product"]:
        if col not in cols:
            conn.execute(f"ALTER TABLE report_imports ADD COLUMN {col} TEXT")
            conn.commit()
            print(f"[OK] {col} 컬럼 추가됨")
        else:
            print(f"[OK] {col} 컬럼 이미 존재")

    companies = conn.execute(
        "SELECT id, company_name, biz_no FROM report_imports ORDER BY id"
    ).fetchall()

    print(f"\n총 {len(companies)}개 기업 정보 수집 시작\n" + "-" * 60)
    success, fail = 0, 0

    for row in companies:
        cid, name, biz_no = row["id"], row["company_name"], row["biz_no"]
        info = fetch_info(biz_no)

        if info["industry"] or info["main_product"]:
            conn.execute(
                "UPDATE report_imports SET industry=?, main_product=? WHERE id=?",
                (info["industry"], info["main_product"], cid),
            )
            conn.commit()
            print(f"  [{cid}] {name:30s} | 업종: {info['industry']} | 주요제품: {info['main_product']}")
            success += 1
        else:
            print(f"  [{cid}] {name:30s} → [FAIL] 조회 실패")
            fail += 1

        time.sleep(0.6)

    conn.close()
    print("-" * 60)
    print(f"\n완료: 성공 {success}개 / 실패 {fail}개")


if __name__ == "__main__":
    main()
