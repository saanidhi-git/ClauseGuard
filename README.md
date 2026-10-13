---
title: ClauseGuard
emoji: 🛡️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Know what you sign - unfair clause detector for agreements
---

# ClauseGuard: Know what you sign

An unfair clause detector for rental agreements, job offer letters and app Terms of Service.
Upload a PDF, DOCX or pasted text and ClauseGuard splits it into clauses, flags risky ones in
14 categories, explains each in plain English, pulls out key facts (rent, deposit, lock-in,
notice period, penalties), gives an overall risk score, answers questions with clause citations
and exports a PDF report.

> ClauseGuard gives information, not legal advice.

---

## Aim

To build a deployable NLP system that reads an agreement and tells a non-lawyer, in plain English, which clauses are risky or unfair and why, before they sign it.

## Problem statement

Students renting a PG or flat, freshers signing offer letters and everyone accepting app terms sign long documents they rarely read. Clauses such as deposit forfeiture, service bonds with large penalties, one-sided notice periods, unilateral changes, arbitration in a far-away city and broad data sharing are easy to miss. Existing research datasets (UNFAIR-ToS) cover only online Terms of Service, not the Indian rental and employment documents our users actually sign.

## Objectives

1. Extract clean text from PDF/DOCX/text and segment it into clauses with page numbers.
2. Classify each clause into 14 risk categories (8 from UNFAIR-ToS + 6 India-specific) using a TF-IDF baseline and a fine-tuned Legal-BERT.
3. Build a small team-authored Indian dataset (ClauseGuard-IN) for the India-specific categories.
4. Score risk per clause and per document, and explain each flagged clause in plain English.
5. Extract key facts (parties, amounts, dates, rent, deposit, lock-in, notice period, penalties).
6. Answer questions about the document using retrieval-augmented generation with clause citations.
7. Evaluate all models honestly and ship the whole thing as one Docker container on Hugging Face Spaces.

## Features

- **One main flow:** upload → report. Drag-and-drop or paste, document-type picker, five built-in samples (three with red flags, two fair documents that score low risk), analysis progress steps.
- **Report:** 0–100 risk gauge with verdict, High/Medium/Low counts, Key Facts card (click a fact to jump to its clause), five-bullet summary, full clause list with risk highlighting and filter chips by level and category.
- **Clause panel:** category badges, what it means, why it matters, the question to ask before signing, and a confidence bar.
- **Ask ClauseGuard:** chat drawer with suggested questions per document type; answers cite clause numbers that scroll to and flash the clause.
- **PDF report** with score gauge, key facts table, flagged clauses, summary and disclaimer.
- **History** of analysed documents with delete.
- **Model Insights:** pipeline, LR vs NB vs Legal-BERT vs hybrid comparison, a plain-language guide to the metrics, confusion matrix viewer, dataset stats, single-clause tester with all models side by side, and the preprocessing view (tokens → lemmas → POS → entities).
- Light theme with dark-mode toggle, mobile responsive, risk colours always paired with an icon and text.
- **Works with no API key.** An optional Groq or Gemini key improves explanations, summaries and answers.

## Architecture

```
Browser ── React SPA ──/api──▶ FastAPI ──▶ NLP pipeline ──▶ SQLite
                                   │          ├─ extract (PyMuPDF / python-docx)
                                   │          ├─ segment (regex + sentence fallback)
                                   │          ├─ classify (Legal-BERT or TF-IDF+LR)
                                   │          ├─ risk + explain (templates / LLM)
                                   │          ├─ key facts (spaCy NER + regex)
                                   │          ├─ summary (TextRank on MiniLM)
                                   │          └─ RAG (MiniLM + FAISS, optional LLM)
                                   └──▶ ReportLab PDF
```

Mermaid system, component and sequence diagrams are in [docs/architecture.md](docs/architecture.md). The numbered algorithm is in [docs/methodology.md](docs/methodology.md).

### Risk scoring formula

- **Clause score** `s = max over predicted labels (severity × probability)`, with severity High = 3, Medium = 2, Low = 1, so `0 ≤ s ≤ 3`.
  Level: **High** if `s ≥ 2.1`, **Medium** if `s > 1.0`, **Low** if `s > 0`, else **Safe**.
- **Document score** `= 100 × (1 − exp(−Σₖ (sₖ / 3) / k / 1.5))`, where `s₁ ≥ s₂ ≥ …` are the clause scores sorted worst first and `k = 1, 2, 3…`.
  The harmonic weights make the worst clauses dominate, several medium clauses still add up, and safe clauses add nothing, so a long document is not "diluted" into looking safe.
  Verdict: ≥ 70 high risk, ≥ 40 moderate, ≥ 15 low, else looks fair.

## Risk categories

| Category | Severity | Applies to | Source |
|---|---|---|---|
| Limitation of liability | Medium | all | UNFAIR-ToS |
| Unilateral termination | High | all | UNFAIR-ToS |
| Unilateral change | Medium | all | UNFAIR-ToS |
| Content removal | Low | ToS | UNFAIR-ToS |
| Contract by using | Low | ToS | UNFAIR-ToS |
| Choice of law | Low | all | UNFAIR-ToS |
| Jurisdiction | Medium | all | UNFAIR-ToS |
| Arbitration | Medium | all | UNFAIR-ToS |
| Service bond / lock-in | High | rental, offer letter | ClauseGuard-IN |
| Deposit forfeiture | High | rental | ClauseGuard-IN |
| One-sided notice | Medium | rental, offer letter | ClauseGuard-IN |
| Rent escalation | Medium | rental | ClauseGuard-IN |
| Non-compete | Medium | offer letter | ClauseGuard-IN |
| Broad data sharing | Medium | ToS, offer letter | ClauseGuard-IN |

Each category's display name, severity, document types, explanation template, "why it matters" and "question to ask" live in `backend/app/nlp/categories.py`.

## Libraries used

| Library | Why |
|---|---|
| FastAPI + Uvicorn | async API with automatic OpenAPI docs at `/api/docs` |
| Pydantic v2 | request validation and friendly errors |
| SQLModel + SQLite | zero-setup storage for documents, clauses, chat and the LLM cache |
| PyMuPDF | fast, accurate PDF text extraction per page |
| python-docx | DOCX paragraphs and tables |
| spaCy `en_core_web_sm` | NER (PERSON, ORG, DATE, GPE) for key facts, POS tags for the preprocessing view |
| NLTK | stopword list and WordNet lemmatizer for the baseline |
| scikit-learn | TF-IDF, Logistic Regression, Naive Bayes, metrics |
| transformers + torch | fine-tuning and CPU inference of Legal-BERT |
| sentence-transformers (MiniLM) | clause embeddings for RAG and TextRank |
| faiss-cpu | fast similarity search over clause embeddings |
| datasets | loading UNFAIR-ToS from LexGLUE |
| ReportLab | PDF report and sample PDFs |
| React + Vite + TypeScript | fast, typed single-page frontend |
| Tailwind CSS | consistent styling, dark mode, responsive layout |
| react-router, lucide-react | routing and icons |

## Dataset details

**UNFAIR-ToS** (LexGLUE, `coastalcph/lex_glue`, config `unfair_tos`): sentences from 50 online Terms of Service labelled with 8 unfair-clause types. Train 5,532 / validation 2,275 / test 1,607 sentences; most sentences have no label. The label order is read from the dataset's features in code.

**ClauseGuard-IN** (our contribution, `data/clauseguard_in*.csv`): 300 team-authored clauses, built by `training/build_clauseguard_in.py` from 138 templates written by the team, based on common Indian templates (11-month leave-and-licence agreements, Model Tenancy Act–style clauses, IT-services offer letters with training bonds, app privacy policies). Each template is rendered 2–3 times with varied wording and values.

- 110 rental, 110 offer letter, 80 app/privacy policy clauses; 107 (36%) are fair/neutral with no label.
- Columns: `text`, `labels` (pipe-separated), `doc_type`, `source` (= `team-authored`), `group` (template id).
- Split 247 train / 53 test, stratified, with all variants of a template on the same side (no near-duplicate leakage).
- All names, addresses and companies are fictional. Nothing was taken from real people's documents.

## Model training

```bash
python training/build_clauseguard_in.py   # writes data/clauseguard_in*.csv
python training/train_baseline.py         # TF-IDF + LR and NB -> backend/models/baseline_*.joblib
python training/finetune_legalbert.py     # Legal-BERT -> backend/models/legalbert/ + thresholds.json (or use the Colab notebook)
python training/evaluate.py               # metrics.json, docs/results.md, docs/figures/
```

- Baselines: TF-IDF (1–2 grams, sublinear tf, min_df 2) + One-vs-Rest Logistic Regression (balanced class weights) and Multinomial Naive Bayes. ClauseGuard-IN rows are repeated 3× to balance UNFAIR-ToS.
- Legal-BERT: `nlpaueb/legal-bert-small-uncased`, multi-label head, BCEWithLogits with a positive-class weight for rare labels, max_len 256, 4 epochs. `training/finetune_legalbert.ipynb` is the same logic for Colab (T4 GPU, a few minutes); the `.py` also runs locally if you have a GPU (on CPU it takes several hours).
- Per-label thresholds are tuned on a dev set (UNFAIR-ToS validation + held-out ClauseGuard-IN templates).
- **Model choice at runtime:** if Legal-BERT and LR are both present the app uses the hybrid (Legal-BERT for the 8 UNFAIR-ToS labels, LR for the 6 India labels).
- **Fallback:** if the Legal-BERT weights are missing, the app uses the LR baseline automatically (a small "baseline model" badge appears on Model Insights only). Missing weights never crash the app.

## Results

Numbers below are copied from [docs/results.md](docs/results.md), which `training/evaluate.py` writes from the saved models.

### UNFAIR-ToS test set (8 labels)

| Model | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |
|---|---|---|---|---|---|---|
| TF-IDF + Logistic Regression | 72.0 | 70.4 | 71.2 | 71.3 | 75.5 | 71.8 |
| TF-IDF + Naive Bayes | 75.8 | 50.5 | 60.7 | 79.0 | 51.5 | 60.4 |
| Legal-BERT (fine-tuned) | 77.5 | 75.8 | 76.6 | 81.5 | 79.7 | 80.2 |
| Hybrid (Legal-BERT + LR) | 77.5 | 75.8 | 76.6 | 81.5 | 79.7 | 80.2 |

Per-label F1 (%):

| Label | Support | TF-IDF + Logistic Regression | TF-IDF + Naive Bayes | Legal-BERT (fine-tuned) | Hybrid (Legal-BERT + LR) |
|---|---|---|---|---|---|
| Limitation of liability | 38 | 74.0 | 68.5 | 68.3 | 68.3 |
| Unilateral termination | 38 | 65.8 | 63.8 | 72.7 | 72.7 |
| Unilateral change | 38 | 70.6 | 34.6 | 74.0 | 74.0 |
| Content removal | 13 | 62.9 | 56.0 | 74.1 | 74.1 |
| Contract by using | 23 | 68.4 | 51.6 | 76.9 | 76.9 |
| Choice of law | 13 | 80.0 | 91.7 | 96.3 | 96.3 |
| Jurisdiction | 16 | 82.3 | 76.9 | 93.8 | 93.8 |
| Arbitration | 7 | 70.6 | 40.0 | 85.7 | 85.7 |

### ClauseGuard-IN test set (14 labels)

| Model | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |
|---|---|---|---|---|---|---|
| TF-IDF + Logistic Regression | 83.3 | 52.6 | 64.5 | 37.8 | 37.0 | 34.1 |
| TF-IDF + Naive Bayes | 90.0 | 47.4 | 62.1 | 33.3 | 25.9 | 27.8 |
| Legal-BERT (fine-tuned) | 66.7 | 31.6 | 42.9 | 13.7 | 21.2 | 16.0 |
| Hybrid (Legal-BERT + LR) | 83.3 | 52.6 | 64.5 | 37.8 | 37.0 | 34.1 |

Per-label F1 (%):

| Label | Support | TF-IDF + Logistic Regression | TF-IDF + Naive Bayes | Legal-BERT (fine-tuned) | Hybrid (Legal-BERT + LR) |
|---|---|---|---|---|---|
| Limitation of liability | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| Unilateral termination | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| Unilateral change | 3 | 0.0 | 0.0 | 0.0 | 0.0 |
| Service bond / lock-in | 11 | 100.0 | 100.0 | 87.0 | 100.0 |
| Deposit forfeiture | 2 | 57.1 | 0.0 | 57.1 | 57.1 |
| One-sided notice | 12 | 50.0 | 50.0 | 0.0 | 50.0 |
| Rent escalation | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| Non-compete | 3 | 100.0 | 100.0 | 0.0 | 100.0 |
| Broad data sharing | 2 | 0.0 | 0.0 | 0.0 | 0.0 |

**Model used by the app: Hybrid.** Legal-BERT is clearly best on the large UNFAIR-ToS set, but with only ~250 Indian training clauses it learned the 6 India-specific labels poorly, where the LR baseline is much stronger. The hybrid uses Legal-BERT for the 8 UNFAIR-ToS labels and LR for the 6 India labels, which gives the best result on both test sets.

Charts: `docs/figures/` (per-label F1 and confusion matrices).

## How to run locally

Requirements: Python 3.11+ (we used 3.13), Node 20+.

```bash
# backend (Windows: .venv\Scripts\activate)
python -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r training/requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; [nltk.download(p) for p in ['punkt','punkt_tab','stopwords','wordnet','omw-1.4']]"

# data, models and samples (the trained models are already in backend/models)
python scripts/make_samples.py

# frontend
cd frontend && npm install && npm run build && cd ..

# run (serves the built app and the API on http://localhost:8000)
python -m uvicorn app.main:app --app-dir backend --port 8000
```

For frontend development with hot reload, run the API on port 8000 and `npm run dev` in `frontend/` (Vite proxies `/api` to it), then open http://localhost:5173.

Tests: `cd backend && python -m pytest -q` (segmentation, key facts, risk scoring, and API smoke tests on all three samples).

Optional LLM: copy `.env.example` to `.env` and set `LLM_PROVIDER=groq` (or `gemini`) and `LLM_API_KEY`. Keys are read from the environment only and are never logged.

## Deployment (Hugging Face Spaces, Docker)

The `Dockerfile` is multi-stage: a Node stage builds the React app; a Python stage installs CPU-only torch and the requirements, downloads `en_core_web_sm`, the NLTK data and MiniLM at build time, copies `backend/` (with the trained models) and the samples, and runs as non-root user 1000 on port 7860. The Python image is 3.13 (instead of 3.11) to match the version the scikit-learn models were pickled with.

```bash
docker build -t clauseguard .
docker run -p 7860:7860 clauseguard
# open http://localhost:7860
```

Push to a Space (create a Docker Space named `clauseguard` on huggingface.co first):

```bash
pip install -U huggingface_hub
huggingface-cli login            # paste your own HF token when asked; never commit it
git lfs install
git clone https://huggingface.co/spaces/<your-username>/clauseguard hf-space
# copy the project into hf-space (without .venv, node_modules, frontend/dist, *.db)
cd hf-space
git lfs track "*.safetensors" "*.joblib"
git add .gitattributes . && git commit -m "Deploy ClauseGuard" && git push
```

Alternatively upload Legal-BERT to the Hub (`huggingface-cli upload <user>/clauseguard-legalbert-small backend/models/legalbert`) and set `LEGALBERT_HUB_ID` in the Space settings instead of pushing the weights with LFS.

## Limitations

- ClauseGuard-IN is small (300 clauses, 53 test) and team-authored, so India-specific scores have high variance and the model has not seen real-world wording variety.
- UNFAIR-ToS covers only English online Terms of Service; rental and employment clauses rely on our small dataset.
- Scanned PDFs (images) are not supported; there is no OCR.
- Segmentation relies on numbering; documents without numbering fall back to sentences.
- The risk score is a heuristic, not a legal judgement, and severities are our own choice.
- Only English documents are supported.

## Disclaimer

ClauseGuard gives information, not legal advice. It can miss risky clauses or flag fair ones. For important decisions, consult a qualified lawyer.

## References

1. I. Chalkidis, A. Jana, D. Hartung, M. Bommarito, I. Androutsopoulos, D. M. Katz, N. Aletras. *LexGLUE: A Benchmark Dataset for Legal Language Understanding in English.* ACL 2022.
2. M. Lippi, P. Pałka, G. Contissa, F. Lagioia, H.-W. Micklitz, G. Sartor, P. Torroni. *CLAUDETTE: an automated detector of potentially unfair clauses in online terms of service.* Artificial Intelligence and Law, 2019.
3. I. Chalkidis, M. Fergadiotis, P. Malakasiotis, N. Aletras, I. Androutsopoulos. *LEGAL-BERT: The Muppets straight out of Law School.* Findings of EMNLP 2020.
4. J. Devlin, M.-W. Chang, K. Lee, K. Toutanova. *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* NAACL 2019.
5. N. Reimers, I. Gurevych. *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP 2019.
6. P. Lewis et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020.
