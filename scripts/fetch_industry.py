import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.reports.services.company_metadata import enrich_company_metadata


def main():
    updated = enrich_company_metadata(force=False, max_workers=4)
    print(f"updated: {len(updated)}")
    for company_id, payload in sorted(updated.items()):
        print(
            f"[{company_id}] 업종={payload.get('industry', '') or '-'} | "
            f"주요제품={payload.get('main_product', '') or '-'}"
        )


if __name__ == "__main__":
    main()
