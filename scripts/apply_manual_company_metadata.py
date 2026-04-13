import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "reports.db"

UPDATES = {
    507: {"industry": "경영 컨설팅업", "main_product": "투자 및 경영컨설팅"},
    520: {"industry": "그 외 자동차용 신품 부품 제조업", "main_product": "변속기, 토크컨버터, 파워트레인 부품"},
    531: {"industry": "운송장비용 이차전지 제조업", "main_product": "차량용 방진부품, 자동차용 배터리(AGM)"},
    537: {"industry": "그 외 기타 금속가공제품 제조업", "main_product": "프레스, 열처리, 반제품 조립"},
    539: {"industry": "열간압연, 압출 및 인발제품 제조업", "main_product": "자동차용 스프링 소재(평강, 환강, 파이프), 겹판스프링"},
    554: {"industry": "그 외 자동차용 신품 부품 제조업", "main_product": "자동차 부품(헤드램프 쉴드, 도어래치 외)"},
    555: {"industry": "자동차 엔진용 신품 부품 제조업", "main_product": "자동차부품"},
    556: {"industry": "자동차 및 트레일러 제조업", "main_product": "휠베어링, 자동차 섀시부품"},
    559: {"industry": "자동차 엔진용 신품 부품 제조업", "main_product": "자동차 엔진 부품"},
    565: {"industry": "그 외 자동차용 신품 부품 제조업", "main_product": "C/MBR, FRT ARM류, SPINDLE PLATE"},
    571: {"industry": "그 외 자동차용 신품 부품 제조업", "main_product": "자동차용 스프링, 시트"},
    579: {"industry": "그 외 자동차용 신품 부품 제조업", "main_product": "파워리프트게이트 시스템, 윈도우 레귤레이터, 럼버서포트, 쿨링팬 모듈"},
    583: {"industry": "기어 및 동력전달장치 제조업", "main_product": "베어링하우징, 베어링강구"},
    587: {"industry": "자동차부품 제조업", "main_product": "모터, 전동식 조향장치, 에어백"},
    588: {"industry": "자동차용 신품 조향장치 및 현가 장치 제조업", "main_product": "제동, 조향, 현가 시스템, ADAS"},
    589: {"industry": "농업 및 임업용 기계 제조업", "main_product": "트랙터, 사출시스템, 특수궤도차량, 전자부품"},
    598: {"industry": "자동차용 신품 의자 제조업", "main_product": "좌석 완제품 및 그 부품의 제조 및 판매"},
}


def main():
    conn = sqlite3.connect(DB_PATH)
    for company_id, payload in UPDATES.items():
        conn.execute(
            "UPDATE report_imports SET industry = ?, main_product = ? WHERE id = ?",
            (payload["industry"], payload["main_product"], company_id),
        )
    conn.commit()
    conn.close()
    print(f"updated: {len(UPDATES)}")


if __name__ == "__main__":
    main()
