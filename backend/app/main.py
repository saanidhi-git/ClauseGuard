"""ClauseGuard FastAPI app: API under /api and the built React app at /."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import chat, documents, insights, reports, samples
from .config import DISCLAIMER, FRONTEND_DIST, llm_enabled
from .db import init_db
from .nlp.classify import ClauseClassifier
from .nlp.preprocess import get_nlp
from .nlp.rag import get_embedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
for noisy in ("httpx", "faiss.loader", "sentence_transformers"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # load everything once so the first request is fast
    init_db()
    ClauseClassifier.get()
    get_nlp()
    get_embedder()
    yield


app = FastAPI(title="ClauseGuard API", version="1.0.0", lifespan=lifespan,
              docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

for r in (documents.router, chat.router, reports.router, samples.router, insights.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": ClauseClassifier.get().model_used, "llm": llm_enabled(), "disclaimer": DISCLAIMER}


if (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        file = (FRONTEND_DIST / path).resolve()
        if path and file.is_file() and FRONTEND_DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
