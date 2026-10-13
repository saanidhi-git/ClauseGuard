# App settings read from environment variables

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


def _load_env_file() -> None:
    # read the .env file if there is one
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_env_file()

MODELS_DIR = Path(os.getenv("MODELS_DIR", BACKEND_DIR / "models"))
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
SAMPLES_DIR = DATA_DIR / "samples"
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", ROOT_DIR / "frontend" / "dist"))
DB_PATH = Path(os.getenv("DB_PATH", BACKEND_DIR / "clauseguard.db"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
LEGALBERT_HUB_ID = os.getenv("LEGALBERT_HUB_ID", "").strip()
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DISABLE_TRANSFORMERS = os.getenv("DISABLE_TRANSFORMERS", "0") == "1"

MAX_UPLOAD_MB = 10
MAX_PAGES = 40
MAX_CHARS = 200_000

DISCLAIMER = "ClauseGuard gives information, not legal advice."


def llm_enabled() -> bool:
    return LLM_PROVIDER in {"groq", "gemini"} and bool(LLM_API_KEY)
