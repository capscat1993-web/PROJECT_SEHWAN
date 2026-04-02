# PROJECT_SEHWAN Command Cheatsheet

## 1) CSV -> SQLite (`reports.db`) import

### A. `csv/` 폴더의 CSV를 전부 import (기본 동작)
```powershell
python ".\import_report_csv.py"
```

### B. 특정 CSV 1개만 import (기본 DB: `.\reports.db`)
```powershell
python ".\import_report_csv.py" ".\csv\20260330_평화홀딩스(주)_new csv.csv"
```

### C. DB 경로 지정해서 import
```powershell
python ".\import_report_csv.py" ".\csv\20260330_평화홀딩스(주)_new csv.csv" --db ".\data\reports.db"
```

## 2) SQLite -> Excel (`reports_by_company.xlsx`) export

### A. 회사별 시트(값만)로 내보내기
```powershell
python ".\export_reports_excel.py" --db ".\reports.db" --out "reports_by_company.xlsx"
```

### B. 회사별 시트에 `report_notes`까지 같이 내보내기
```powershell
python ".\export_reports_excel.py" --db ".\reports.db" --out "reports_by_company.xlsx" --include-notes
```

## 3) Git 저장(커밋)

### A. (처음이라면) 저장소 초기화
```powershell
git init
```

### B. 변경사항 확인
```powershell
git status
```

### C. 모두 스테이징
```powershell
git add -A
```

### D. 커밋
```powershell
git commit -m "Update reports import/export"
```

