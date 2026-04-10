# PROJECT_SEHWAN Command Cheatsheet

## 1) CSV -> SQLite import

### `csv/` 폴더 전체 import

```powershell
python ".\scripts\import_report_csv.py"
```

### 특정 CSV 1개 import

```powershell
python ".\scripts\import_report_csv.py" ".\csv\sample.csv"
```

### DB 경로를 직접 지정해서 import

```powershell
python ".\scripts\import_report_csv.py" ".\csv\sample.csv" --db ".\data\reports.db"
```

## 2) SQLite -> Excel export

### 회사별 시트 export

```powershell
python ".\scripts\export_reports_excel.py"
```

기본 출력 파일:

```text
.\runtime\exports\reports_by_company.xlsx
```

### 주석까지 포함해서 export

```powershell
python ".\scripts\export_reports_excel.py" --include-notes
```

## 3) 로컬 백엔드 실행

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\run-dev.ps1"
```

## 4) 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest
```
