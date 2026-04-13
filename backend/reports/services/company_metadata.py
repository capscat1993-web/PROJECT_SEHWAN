import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from ..paths import DB_PATH

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    cleaned = " ".join(value.replace("\xa0", " ").split())
    cleaned = cleaned.split("통신판매업번호", 1)[0].strip(" :,-|>")
    return cleaned


def _strip_stop_tokens(value: str) -> str:
    cleaned = value
    for token in ("기업규모", "업종분류", "업종", "업태", "종목", "사업자", "현재 상태", "회사명"):
        cleaned = re.split(rf"\s*{re.escape(token)}\s*[:：]", cleaned, maxsplit=1)[0]
    return _clean_text(cleaned)


def _extract_labeled_value(text: str, labels: list[str], stop_tokens: list[str]) -> str:
    stop_pattern = "|".join(re.escape(token) for token in stop_tokens)
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:：]\s*(.+?)(?=\s*(?:{stop_pattern})\s*[:：]|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _strip_stop_tokens(match.group(1))
    return ""


def _normalize_industry(value: str) -> str:
    cleaned = _clean_text(value)
    if ">" in cleaned:
        parts = [part.strip(" :-") for part in cleaned.split(">") if part.strip(" :-")]
        if parts:
            cleaned = parts[-1]
    return cleaned


def _extract_metadata_from_html(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    meta_description = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    description = meta_description.get("content", "") if meta_description else ""
    text = _clean_text(soup.get_text("\n", strip=True))

    industry = _extract_labeled_value(
        description,
        ["업종분류", "업종", "업태"],
        ["현재 상태", "사업자", "회사명", "기업규모", "주요제품", "주요 제품", "종목"],
    )
    main_product = _extract_labeled_value(
        description,
        ["주요제품", "주요 제품", "종목"],
        ["현재 상태", "사업자", "회사명", "기업규모", "업종분류", "업종", "업태"],
    )

    if not industry:
        line_match = re.search(r"업종\s*\n\s*([^\n]+)", text)
        if line_match:
            industry = line_match.group(1)
    if not main_product:
        line_match = re.search(r"주요제품\s*\n\s*([^\n]+)", text)
        if line_match:
            main_product = line_match.group(1)

    return {
        "industry": _normalize_industry(industry),
        "main_product": _clean_text(main_product),
    }


def _fetch_company_metadata(biz_no: str) -> dict[str, str]:
    biz_no = "".join(ch for ch in (biz_no or "") if ch.isdigit())
    if not biz_no:
        return {"industry": "", "main_product": ""}

    session = requests.Session()
    session.trust_env = False
    response = session.get(
        f"https://bizno.net/article/{biz_no}",
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    return _extract_metadata_from_html(response.text)


def enrich_company_metadata(
    *,
    limit: int | None = None,
    force: bool = False,
    company_ids: list[int] | None = None,
    max_workers: int = 4,
) -> dict[int, dict[str, str]]:
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    where_clauses: list[str] = []
    params: list[object] = []

    if company_ids:
        placeholders = ",".join("?" for _ in company_ids)
        where_clauses.append(f"id IN ({placeholders})")
        params.extend(company_ids)

    if not force:
        where_clauses.append(
            "(COALESCE(TRIM(industry), '') = '' OR COALESCE(TRIM(main_product), '') = '')"
        )

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    limit_sql = f" LIMIT {int(limit)}" if limit else ""
    rows = conn.execute(
        "SELECT id, company_name, biz_no, industry, main_product "
        f"FROM report_imports {where_sql} ORDER BY id{limit_sql}",
        params,
    ).fetchall()

    updates: dict[int, dict[str, str]] = {}
    if not rows:
        conn.close()
        return updates

    def worker(row):
        payload = _fetch_company_metadata(row["biz_no"])
        return row, payload

    try:
        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            futures = [executor.submit(worker, row) for row in rows]
            for future in as_completed(futures):
                row, payload = future.result()
                industry = _clean_text(row["industry"]) if row["industry"] and not force else ""
                main_product = _clean_text(row["main_product"]) if row["main_product"] and not force else ""
                next_industry = industry or payload.get("industry", "")
                next_main_product = main_product or payload.get("main_product", "")

                if not next_industry and not next_main_product:
                    continue

                conn.execute(
                    "UPDATE report_imports SET industry = ?, main_product = ? WHERE id = ?",
                    (next_industry or None, next_main_product or None, row["id"]),
                )
                updates[row["id"]] = {
                    "industry": next_industry,
                    "main_product": next_main_product,
                }
        conn.commit()
    finally:
        conn.close()

    return updates
