"""FastAPI 入口 — 墨韵书境后端"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import ALLOWED_ORIGINS
from .database import SessionLocal, init_db
from .api import novels, chat, stories
from .services import novel_service


def create_app() -> FastAPI:
    app = FastAPI(
        title="墨韵书境 InkRealm API",
        description="沉浸式 AI 角色互动 + 小说共创平台",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(novels.router)
    app.include_router(chat.router)
    app.include_router(stories.router)

    @app.on_event("startup")
    def _on_startup() -> None:
        init_db()
        with SessionLocal() as db:
            novel_service.ensure_seed_novel(db)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "service": "InkRealm"}

    # ---------------- 静态前端托管 ----------------
    # 生产部署时,前端构建产物放在 frontend/dist/
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dist / "assets")),
            name="assets",
        )

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            # 让前端路由生效:任何不匹配的 path 都返回 index.html
            if full_path.startswith("api/"):
                return {"detail": "Not Found"}
            index_html = frontend_dist / "index.html"
            if index_html.exists():
                return FileResponse(index_html)
            return {"detail": "Frontend not built. cd frontend && npm install && npm run build"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
