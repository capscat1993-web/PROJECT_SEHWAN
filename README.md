# PROJECT_SEHWAN

자동차 부품사 재무 리포트를 조회하고 분석하는 `Django 백엔드 + Next.js 프론트엔드` 프로젝트입니다.

## 구조

- `backend/`: Django API 서버
- `frontend/`: Next.js App Router 프론트엔드
- `data/`: SQLite DB (`reports.db`)
- `scripts/`: CSV 적재, 업종 수집, 엑셀 export 스크립트
- `docs/`, `logos/`: 기획 문서 및 디자인 자산

## 현재 DB 스키마

SQLite DB `data/reports.db` 기준 핵심 테이블:

- `report_imports`: 회사 기본정보, 보고일, 업종, 주요제품
- `report_notes`: 보고서에서 추출한 설명 메모
- `report_values`: 섹션별 재무 수치 원본

## 로컬 실행

### 1. 백엔드

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\backend\manage.py runserver
```

기본 주소: `http://127.0.0.1:8000`

권장 환경 변수:

- `DB_PATH`
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `CORS_ORIGINS`
- `DJANGO_ALLOWED_HOSTS`

### 2. 프론트엔드

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

기본 주소: `http://127.0.0.1:3000`

필수 환경 변수:

- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- `API_BASE_URL=http://127.0.0.1:8000`

## 주요 API

- `GET /api/overview`
- `GET /api/companies`
- `GET /api/companies/{id}`
- `GET /api/companies/{id}/dashboard`
- `GET /api/companies/{id}/health`
- `GET /api/companies/{id}/health/export`
- `POST /api/chat`

## 데이터 스크립트

CSV 적재:

```powershell
python .\scripts\import_report_csv.py
```

업종/주요제품 수집:

```powershell
python .\scripts\fetch_industry.py
```

회사별 엑셀 export:

```powershell
python .\scripts\export_reports_excel.py --include-notes
```

## 배포

### 백엔드

- `render.yaml`은 Render Web Service 기준입니다.
- 시작 명령은 `backend/` 기준 Django WSGI 서버를 사용합니다.
- 배포 환경변수 예시:
  - `DB_PATH=/opt/render/project/src/data/reports.db`
  - `CORS_ORIGINS=https://your-frontend-domain.vercel.app`
  - `DJANGO_ALLOWED_HOSTS=*`

### 프론트엔드

- `frontend/`를 기준 디렉터리로 배포합니다.
- Vercel 배포를 전제로 `npm install && npm run build` 를 사용하면 됩니다.
- 환경 변수:
  - `NEXT_PUBLIC_API_BASE_URL=<배포된 백엔드 URL>`
  - `API_BASE_URL=<배포된 백엔드 URL>`
