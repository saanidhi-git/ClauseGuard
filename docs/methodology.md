# Methodology

## A. Data preparation

1. Load UNFAIR-ToS from LexGLUE (`coastalcph/lex_glue`, config `unfair_tos`). Read the 8 label names from the dataset features and map them by name to ClauseGuard's label keys (the order is never assumed).
2. Build ClauseGuard-IN (`training/build_clauseguard_in.py`): 138 team-authored clause templates for Indian rental agreements, offer letters and app policies. Each template is rendered 2-3 times with different wording choices and slot values (amounts, durations, cities, names) to give 300 clauses (110 rental, 110 offer letter, 80 app policy; 36% fair/neutral with no label).
3. Split ClauseGuard-IN 80/20, stratified by document type and first label, keeping all variants of a template on the same side (group split) so test clauses are never near-copies of training clauses.
4. Merge both datasets into one 14-label multi-hot space. UNFAIR-ToS rows have 0 for the 6 India-specific labels. ClauseGuard-IN training rows are repeated 3 times to balance the much larger UNFAIR-ToS set.

## B. Preprocessing (baseline models)

5. Normalise text: Unicode NFKC, map ₹ / Rs. to "inr", lowercase, remove quotes, squeeze spaces.
6. Tokenize with a regex tokenizer (words and numbers like 2,00,000).
7. Remove NLTK English stopwords, but keep words that change legal meaning (not, no, without, any, only, before, after).
8. Lemmatize with WordNet (verb, then noun).

## C. Model training

9. Baseline 1: TF-IDF (word 1-2 grams, sublinear tf, min_df = 2) + One-vs-Rest Logistic Regression (class_weight = balanced, C = 4).
10. Baseline 2: the same TF-IDF + One-vs-Rest Multinomial Naive Bayes (alpha = 0.1).
11. Legal-BERT: `nlpaueb/legal-bert-small-uncased` with a 14-way sigmoid head, BCEWithLogits loss with pos_weight = clip(sqrt(neg/pos), 1, 15), AdamW (lr 5e-5, weight decay 0.01), linear warm-up/decay, max length 256, batch 16, 4 epochs; keep the epoch with the best dev micro-F1.
12. Threshold tuning: for each label, pick the threshold in [0.30, 0.90] that maximises F1 on the dev set (UNFAIR-ToS validation + held-out ClauseGuard-IN templates). Save to the model bundle / `thresholds.json`.
13. Refit the baselines on all training data with the tuned thresholds.

## D. Inference pipeline (per document)

14. Extract text: PyMuPDF for PDF (reject files with almost no text as scanned PDFs), python-docx for DOCX. Remove lines that repeat at the top/bottom of most pages (headers/footers), page-number lines, and join hyphenated line breaks. Keep a (start, end, page) span for every page.
15. Segment into clauses: start a new clause at numbered headings (`1.`, `1.1`, `(a)`, `iv)`, `Clause 5`, `Article 2`); if fewer than 3 headings exist, fall back to paragraph and sentence splitting. Merge pieces under 6 words into the next clause; split clauses over 120 words at sentence boundaries. Separate leading ALL-CAPS headings.
16. Classify all clauses in one batch with the primary model: the hybrid (Legal-BERT probabilities for the 8 UNFAIR-ToS labels, LR probabilities for the 6 India labels, chosen because each is better on its own label group) when both exist, otherwise LR. Keep labels whose probability ≥ the label's threshold, and drop labels that do not apply to the chosen document type.
17. Clause risk: `s = max over predicted labels (severity × probability)`, severity High = 3, Medium = 2, Low = 1. Level: High if s ≥ 2.1, Medium if s > 1.0, Low if s > 0, otherwise Safe.
18. Document score: sort clause scores from worst to best and compute `100 × (1 − exp(−Σ_k (s_k / 3) / k / 1.5))`, k = 1, 2, 3… The harmonic weights make the worst clauses dominate, and safe clauses add nothing, so long fair documents are not diluted into looking safe.
19. Explanations: fill the category template with the clause's own amount, period and percentage (regex). If an LLM key is set, rewrite with a strict JSON prompt that forbids new facts (max 60 words), cached in SQLite by hash.
20. Key facts: regex rules for ₹/Rs./INR amounts, durations ("11 (eleven) months", "90 days") and percentages, triggered by keywords (rent, security deposit, lock-in, notice, penalty, bond, CTC, probation) plus spaCy NER for parties (PERSON/ORG), dates and places. Each fact keeps the clause id it came from.
21. Summary: TextRank (PageRank with damping 0.85) on the cosine-similarity graph of MiniLM clause embeddings, with a small boost for High/Medium clauses; the top 5 are shown in document order.

## E. Question answering (RAG)

22. Embed every clause with `all-MiniLM-L6-v2` (normalised) and store it in a per-document FAISS inner-product index.
23. Embed the question, retrieve the top 3 clauses.
24. Without an LLM: show each clause's best-matching sentence (highest cosine similarity to the question). If the best score is below 0.2, say the document may not cover it.
25. With an LLM: answer only from the 3 clauses, cite clause numbers, and reply "The document doesn't say." when the answer is not there.

## F. Evaluation

26. Evaluate all models on the UNFAIR-ToS test set (8 labels) and the ClauseGuard-IN test set (14 labels) with micro and macro precision, recall and F1, per-label F1 and per-label confusion matrices (`training/evaluate.py`). Results are written to `docs/results.md` and `backend/models/metrics.json`.
