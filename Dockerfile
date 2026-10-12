# ---------- 1. build the React app ----------
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 2. Python API + models ----------
# same Python version the models were trained with, so the saved sklearn models load cleanly
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    NLTK_DATA=/app/.cache/nltk_data \
    DB_PATH=/app/data/clauseguard.db

RUN useradd -m -u 1000 user
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r backend/requirements.txt

# download every model at build time so the first request never waits for a download
RUN python -m spacy download en_core_web_sm \
 && python -c "import nltk; [nltk.download(p, download_dir='/app/.cache/nltk_data', quiet=True) for p in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4']]" \
 && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY backend/ backend/
COPY data/samples/ data/samples/
COPY --from=web /web/dist frontend/dist

RUN rm -rf backend/tests backend/*.db && chown -R user:user /app
USER user

EXPOSE 7860
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
