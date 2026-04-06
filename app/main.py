import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import companies, financial, analysis, chat

BASE_DIR = os.path.dirname(__file__)

app = FastAPI(title="기업 재무정보 서비스")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(companies.router)
app.include_router(financial.router)
app.include_router(analysis.router)
app.include_router(chat.router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
