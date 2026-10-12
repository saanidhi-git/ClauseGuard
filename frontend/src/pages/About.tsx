import { Brain, Database, FileUp, ListChecks, MessageCircle, ScanSearch, ShieldAlert } from "lucide-react";

const STEPS = [
  { icon: FileUp, title: "Read", text: "Text is extracted from the PDF, DOCX or pasted text, removing headers, footers and page numbers while keeping track of page numbers." },
  { icon: ScanSearch, title: "Split & classify", text: "The document is split into clauses, and each clause is checked against 14 risk categories by a trained classifier." },
  { icon: ListChecks, title: "Score & explain", text: "Risky clauses are scored, explained in plain English, and key facts like rent, deposit and notice period are pulled out." },
  { icon: MessageCircle, title: "Ask", text: "Questions are answered from the most relevant clauses only (retrieval-augmented), with clause numbers as citations." },
];

const CATEGORIES = [
  ["Limitation of liability", "The other side avoids responsibility for losses"],
  ["Unilateral termination", "The other side can end the agreement on its own"],
  ["Unilateral change", "Terms can be changed without your consent"],
  ["Content removal", "Your content or account can be deleted at will"],
  ["Contract by using", "Just using the service counts as agreeing"],
  ["Choice of law", "Disputes follow a far-away or foreign law"],
  ["Jurisdiction", "Cases can be filed only in a distant court"],
  ["Arbitration", "Disputes go to private arbitration, not court"],
  ["Service bond / lock-in", "Penalty for leaving before a fixed period"],
  ["Deposit forfeiture", "The security deposit can be kept"],
  ["One-sided notice", "You must give longer notice than the other side"],
  ["Rent escalation", "Rent can rise steeply or at the owner's choice"],
  ["Non-compete", "Restrictions on joining other employers"],
  ["Broad data sharing", "Personal data shared widely with third parties"],
];

const TECH = [
  { icon: Brain, title: "NLP models", text: "TF-IDF with Logistic Regression and Naive Bayes as baselines, and a fine-tuned Legal-BERT (small) for multi-label clause classification." },
  { icon: Database, title: "Data", text: "UNFAIR-ToS from the LexGLUE benchmark for the 8 standard categories, plus ClauseGuard-IN, a set of Indian rental, offer-letter and app-policy clauses for the 6 India-specific categories." },
  { icon: ScanSearch, title: "Language processing", text: "spaCy for named entities and part-of-speech tags, NLTK for stopwords and lemmatization, regular expressions for Indian amounts and durations." },
  { icon: MessageCircle, title: "Retrieval", text: "MiniLM sentence embeddings with a FAISS index per document power the Q&A and the TextRank summary." },
];

const REFS = [
  "I. Chalkidis et al. LexGLUE: A Benchmark Dataset for Legal Language Understanding in English. ACL 2022.",
  "M. Lippi et al. CLAUDETTE: an automated detector of potentially unfair clauses in online terms of service. Artificial Intelligence and Law, 2019.",
  "I. Chalkidis et al. LEGAL-BERT: The Muppets straight out of Law School. Findings of EMNLP 2020.",
  "J. Devlin et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL 2019.",
  "N. Reimers and I. Gurevych. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP 2019.",
  "P. Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.",
];

export default function About() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-3xl font-bold text-slate-900 dark:text-white">About ClauseGuard</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-400">
        An NLP project that detects unfair or risky clauses in agreements and explains them in plain English.
      </p>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">The problem</h2>
        <p className="mt-2 leading-relaxed text-slate-600 dark:text-slate-300">
          Students renting a PG or flat, freshers signing their first offer letter and everyone tapping "I agree" on app
          terms sign documents they rarely read in full. Hidden in them are clauses like deposit forfeiture, service
          bonds with large penalties, one-sided notice periods and broad data sharing. ClauseGuard reads the document,
          flags these clauses and explains what they mean before you sign.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">How it works</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {STEPS.map((s, i) => (
            <div key={s.title} className="card p-5">
              <div className="flex items-center gap-2">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent-50 text-accent-600 dark:bg-accent-600/15">
                  <s.icon className="h-4 w-4" aria-hidden />
                </span>
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  {i + 1}. {s.title}
                </h3>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">What it detects</h2>
        <div className="card mt-3 grid gap-x-6 p-5 sm:grid-cols-2">
          {CATEGORIES.map(([name, text]) => (
            <div key={name} className="border-b border-slate-100 py-2 last:border-0 dark:border-slate-800">
              <p className="text-sm font-medium text-slate-900 dark:text-white">{name}</p>
              <p className="text-xs text-slate-500">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Under the hood</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {TECH.map((t) => (
            <div key={t.title} className="card p-5">
              <h3 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
                <t.icon className="h-4 w-4 text-accent-600" aria-hidden /> {t.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="card mt-8 flex gap-3 border-amber-200 bg-amber-50 p-5 dark:border-amber-900 dark:bg-amber-950/30">
        <ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" aria-hidden />
        <div>
          <h2 className="font-semibold text-amber-900 dark:text-amber-200">Disclaimer</h2>
          <p className="mt-1 text-sm text-amber-900/80 dark:text-amber-200/80">
            ClauseGuard gives information, not legal advice. It can miss risky clauses or flag fair ones. For important
            decisions, consult a qualified lawyer.
          </p>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">References</h2>
        <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm text-slate-600 dark:text-slate-400">
          {REFS.map((r) => <li key={r}>{r}</li>)}
        </ol>
      </section>
    </div>
  );
}
