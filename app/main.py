import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db.database import init_db
from app.security.keystore import get_session_secret
from app.web.routers import connections, dashboard

logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="CX-View")
app.add_middleware(SessionMiddleware, secret_key=get_session_secret())
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(connections.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
