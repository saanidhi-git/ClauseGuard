import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Download, FileText, ListChecks, Loader2, MessageCircle, Sparkles } from "lucide-react";
import { api, type DocDetail, type Level } from "../api";
import { Gauge, LEVEL_STYLE, RiskBadge, scoreLevel } from "../components/Risk";
import ClausePanel from "../components/ClausePanel";
import ChatDrawer from "../components/ChatDrawer";

const LEVELS: Level[] = ["High", "Medium", "Low", "Safe"];

export default function Report() {
  const { id } = useParams();
  const docId = Number(id);
  const [doc, setDoc] = useState<DocDetail | null>(null);
  const [error, setError] = useState("");
  const [levelFilter, setLevelFilter] = useState<Level | "All">("All");
  const [catFilter, setCatFilter] = useState<string>("All");
  const [selected, setSelected] = useState<number | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [flashId, setFlashId] = useState<number | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let stop = false;
    const load = () =>
      api
        .get(docId)
        .then((d) => {
          if (stop) return;
          setDoc(d);
          if (d.status === "processing") timer = setTimeout(load, 2000);
        })
        .catch((e) => !stop && setError(e.message));
    load();
    return () => {
      stop = true;
      clearTimeout(timer);
    };
  }, [docId]);

  const categories = useMemo(() => {
    const m = new Map<string, string>();
    doc?.clauses.forEach((c) => c.labels.forEach((l, i) => m.set(l, c.label_names[i])));
    return [...m.entries()];
  }, [doc]);

  const visible = useMemo(
    () =>
      (doc?.clauses ?? []).filter(
        (c) => (levelFilter === "All" || c.risk_level === levelFilter) && (catFilter === "All" || c.labels.includes(catFilter)),
      ),
    [doc, levelFilter, catFilter],
  );

  const goToClause = useCallback((cid: number) => {
    setLevelFilter("All");
    setCatFilter("All");
    setTimeout(() => {
      document.getElementById(`clause-${cid}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      setFlashId(cid);
      setTimeout(() => setFlashId(null), 3000);
    }, 50);
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-red-500" aria-hidden />
        <h1 className="mt-3 text-xl font-semibold">We couldn't open this report</h1>
        <p className="mt-1 text-slate-500">{error}</p>
        <Link to="/" className="btn-primary mt-6">Analyse a document</Link>
      </div>
    );
  }

  if (!doc || doc.status === "processing") return <ReportSkeleton processing={doc?.status === "processing"} />;

  if (doc.status === "error") {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-red-500" aria-hidden />
        <h1 className="mt-3 text-xl font-semibold">Analysis failed</h1>
        <p className="mt-1 text-slate-500">{doc.error}</p>
        <Link to="/" className="btn-primary mt-6">Try another document</Link>
      </div>
    );
  }

  const level = scoreLevel(doc.score);
  const selectedClause = doc.clauses.find((c) => c.id === selected) ?? null;
  const facts = Object.entries(doc.key_facts);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-accent-600">
            <ArrowLeft className="h-4 w-4" aria-hidden /> New analysis
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">{doc.title}</h1>
          <p className="text-sm text-slate-500">
            {doc.doc_type_name} · {doc.page_count} page{doc.page_count === 1 ? "" : "s"} · {doc.clauses.length} clauses ·{" "}
            {new Date(doc.created_at).toLocaleString()}
          </p>
        </div>
        <a href={api.reportUrl(doc.id)} className="btn-primary" download>
          <Download className="h-4 w-4" aria-hidden /> Download PDF report
        </a>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <section className="card fade-up flex flex-col items-center p-6 text-center" aria-label="Risk score">
          <h2 className="self-start text-sm font-semibold text-slate-500">Overall risk</h2>
          <Gauge score={doc.score} />
          <p className={`mt-1 font-semibold ${LEVEL_STYLE[level].text}`}>{doc.verdict}</p>
          <div className="mt-5 grid w-full grid-cols-3 gap-2">
            {(["High", "Medium", "Low"] as Level[]).map((lv) => {
              const s = LEVEL_STYLE[lv];
              const Icon = s.icon;
              return (
                <button
                  key={lv}
                  onClick={() => setLevelFilter(lv)}
                  className={`rounded-xl p-3 ${s.bg} transition hover:brightness-95`}
                  aria-label={`Show ${lv} risk clauses`}
                >
                  <Icon className={`mx-auto h-4 w-4 ${s.text}`} aria-hidden />
                  <p className={`text-2xl font-bold ${s.text}`}>{doc.level_counts[lv] ?? 0}</p>
                  <p className={`text-xs ${s.text}`}>{lv}</p>
                </button>
              );
            })}
          </div>
        </section>

        <section className="card fade-up p-6" aria-label="Key facts">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <ListChecks className="h-4 w-4" aria-hidden /> Key facts
          </h2>
          {facts.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">No amounts, dates or periods were found.</p>
          ) : (
            <dl className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
              {facts.map(([k, f]) => (
                <div key={k} className="flex items-start justify-between gap-3 py-2">
                  <dt className="text-sm text-slate-500">{f.label}</dt>
                  <dd className="text-right text-sm font-medium text-slate-900 dark:text-white">
                    <button onClick={() => goToClause(f.clause_id)} className="text-right hover:text-accent-600" title="Show clause">
                      {Array.isArray(f.value) ? f.value.join(", ") : f.value}
                    </button>
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </section>

        <section className="card fade-up p-6" aria-label="Summary">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <FileText className="h-4 w-4" aria-hidden /> Summary
          </h2>
          <ul className="mt-3 space-y-2.5">
            {doc.summary.map((s, i) => (
              <li key={i} className="flex gap-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-500" aria-hidden />
                {s}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="mt-8" aria-label="Clauses">
        <div className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Document clauses</h2>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by risk level">
            {(["All", ...LEVELS] as const).map((lv) => {
              const count = lv === "All" ? doc.clauses.length : doc.level_counts[lv] ?? 0;
              const active = levelFilter === lv;
              return (
                <button
                  key={lv}
                  onClick={() => setLevelFilter(lv)}
                  aria-pressed={active}
                  className={`rounded-full border px-3 py-1 text-sm transition ${
                    active
                      ? "border-accent-600 bg-accent-600 text-white"
                      : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900"
                  }`}
                >
                  {lv} <span className="opacity-70">({count})</span>
                </button>
              );
            })}
          </div>
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
              {[["All", "All categories"], ...categories].map(([key, name]) => (
                <button
                  key={key}
                  onClick={() => setCatFilter(key)}
                  aria-pressed={catFilter === key}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                    catFilter === key
                      ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="mt-4 space-y-2.5">
          {visible.length === 0 && (
            <div className="card p-8 text-center text-sm text-slate-500">No clauses match these filters.</div>
          )}
          {visible.map((c) => {
            const s = LEVEL_STYLE[c.risk_level];
            const risky = c.risk_level !== "Safe";
            return (
              <button
                id={`clause-${c.id}`}
                key={c.id}
                onClick={() => setSelected(c.id)}
                className={`block w-full rounded-xl border-l-4 p-4 text-left transition hover:shadow-md ${
                  risky ? `${s.border} ${s.bg}` : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                } ${selected === c.id ? "ring-2 ring-accent-500" : ""} ${flashId === c.id ? "flash" : ""}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">Clause {c.number}</span>
                  {c.heading && <span className="text-sm text-slate-500">· {c.heading}</span>}
                  <span className="text-xs text-slate-400">p. {c.page}</span>
                  <span className="ml-auto">{risky ? <RiskBadge level={c.risk_level} small /> : null}</span>
                </div>
                <p className={`mt-1.5 text-sm leading-relaxed ${risky ? "text-slate-800 dark:text-slate-200" : "text-slate-600 dark:text-slate-400"}`}>
                  {c.text}
                </p>
                {risky && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {c.label_names.map((n) => (
                      <span key={n} className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-900/60 dark:text-slate-300">
                        {n}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>
        <p className="mt-6 text-center text-xs text-slate-500">{doc.disclaimer}</p>
      </section>

      {!chatOpen && (
        <button
          onClick={() => {
            setSelected(null);
            setChatOpen(true);
          }}
          className="btn-primary fixed bottom-5 right-5 z-30 rounded-full px-5 py-3 shadow-lg"
        >
          <MessageCircle className="h-5 w-5" aria-hidden /> Ask ClauseGuard
        </button>
      )}

      {selectedClause && !chatOpen && <ClausePanel clause={selectedClause} onClose={() => setSelected(null)} />}
      {chatOpen && (
        <ChatDrawer
          docId={doc.id}
          docType={doc.doc_type}
          clauses={doc.clauses}
          onClose={() => setChatOpen(false)}
          onCite={(cid) => {
            if (window.innerWidth < 1024) setChatOpen(false);
            goToClause(cid);
          }}
        />
      )}
    </div>
  );
}

function ReportSkeleton({ processing }: { processing: boolean }) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8" aria-busy="true">
      {processing && (
        <div className="card mb-6 flex items-center gap-3 p-4 text-sm">
          <Loader2 className="h-5 w-5 animate-spin text-accent-600" aria-hidden />
          This is a long document, so it is being analysed in the background. The report will appear automatically.
          <Sparkles className="ml-auto h-4 w-4 text-accent-500" aria-hidden />
        </div>
      )}
      <div className="skeleton h-8 w-72" />
      <div className="skeleton mt-2 h-4 w-48" />
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        {[0, 1, 2].map((i) => <div key={i} className="skeleton h-64" />)}
      </div>
      <div className="mt-8 space-y-3">
        {[0, 1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-20" />)}
      </div>
    </div>
  );
}
