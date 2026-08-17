from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import auth, briefing, demo, github, invites, me, projects, teams, timeline
from app.worker.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="너머 (Neomeo) API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(teams.router)
app.include_router(invites.router)
app.include_router(projects.router)
app.include_router(github.router)
app.include_router(timeline.router)
app.include_router(briefing.router)
app.include_router(demo.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


_dist = (Path(__file__).parent.parent.parent / "frontend" / "dist").resolve()
if _dist.exists():
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # full_path는 사용자가 URL로 직접 조작 가능한 값이라, "../"를 검증 없이 그대로
        # 이어붙이면 dist 밖(백엔드 소스, .env 등)을 읽어버리는 경로 순회 취약점이 된다.
        # resolve() 후 dist 하위인지 반드시 확인한다.
        target = (_dist / full_path).resolve()
        if target.is_relative_to(_dist) and target.is_file():
            return FileResponse(str(target))
        return FileResponse(str(_dist / "index.html"))
