import { useEffect, useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, Briefcase, CheckCircle2, Check, FileText, FileUp, Home as HomeIcon, Loader2, ScrollText, ShieldCheck, Sparkles, Type, Upload,
} from "lucide-react";
import { api, DOC_TYPES, type DocType, type Sample } from "../api";
import { useToast } from "../components/Toast";

const STEPS = ["Reading", "Splitting clauses", "Checking risks", "Extracting key facts"];
const TYPE_ICON = { rental: HomeIcon, offer_letter: Briefcase, tos: ScrollText };
const MAX_MB = 10;
const GROUPS = [
  { kind: "risky", label: "Documents with red flags", icon: AlertTriangle, color: "text-amber-700 dark:text-amber-300" },
  { kind: "fair", label: "Fair, balanced documents", icon: CheckCircle2, color: "text-green-700 dark:text-green-300" },
] as const;

export default function Home() {
  const nav = useNavigate();
  const toast = useToast();
  const [docType, setDocType] = useState<DocType>("rental");
  const [tab, setTab] = useState<"upload" | "paste">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [samples, setSamples] = useState<Sample[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.samples().then(setSamples).catch(() => setSamples([]));
  }, []);

  // move the progress steps forward while the request runs
  useEffect(() => {
    if (!busy) return;
    setStep(0);
    const t = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 900);
    return () => clearInterval(t);
  }, [busy]);

  const pickFile = (f: File | undefined) => {
    if (!f) return;
    if (!/\.(pdf|docx|txt)$/i.test(f.name)) return toast("Please choose a PDF, DOCX or TXT file.", "error");
    if (f.size > MAX_MB * 1024 * 1024) return toast(`The file is larger than ${MAX_MB} MB.`, "error");
    setFile(f);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    pickFile(e.dataTransfer.files?.[0]);
  };

  const run = async (fn: () => Promise<{ document_id: number }>) => {
    setBusy(true);
    try {
      const { document_id } = await fn();
      setStep(STEPS.length);
      nav(`/report/${document_id}`);
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  };

  const analyze = () => {
    if (tab === "upload") {
      if (!file) return toast("Choose a file first.", "error");
      run(() => api.uploadFile(file, docType, title));
    } else {
      if (text.trim().split(/\s+/).length < 5) return toast("Please paste the agreement text (at least a few lines).", "error");
      run(() => api.uploadText(text, docType, title));
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14">
      <section className="fade-up text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-50 px-3 py-1 text-xs font-medium text-accent-700 dark:bg-accent-600/15 dark:text-accent-100">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden /> Unfair clause detector for Indian agreements
        </span>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-white">Know what you sign</h1>
        <p className="mx-auto mt-3 max-w-2xl text-slate-600 dark:text-slate-400">
          Upload a rental agreement, job offer letter or app's terms. ClauseGuard finds risky clauses, explains them in
          plain English, pulls out the key facts and answers your questions.
        </p>
      </section>

      <section className="card fade-up mt-10 p-5 sm:p-7" aria-label="Analyse a document">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white">1. What are you signing?</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-3" role="radiogroup">
          {DOC_TYPES.map((d) => {
            const Icon = TYPE_ICON[d.key];
            const active = docType === d.key;
            return (
              <button
                key={d.key}
                role="radio"
                aria-checked={active}
                onClick={() => setDocType(d.key)}
                className={`flex items-start gap-3 rounded-xl border p-4 text-left transition ${
                  active
                    ? "border-accent-600 bg-accent-50 ring-1 ring-accent-600 dark:bg-accent-600/10"
                    : "border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600"
                }`}
              >
                <Icon className={`mt-0.5 h-5 w-5 ${active ? "text-accent-600" : "text-slate-400"}`} aria-hidden />
                <span>
                  <span className="block text-sm font-medium text-slate-900 dark:text-white">{d.name}</span>
                  <span className="block text-xs text-slate-500">{d.hint}</span>
                </span>
              </button>
            );
          })}
        </div>

        <h2 className="mt-7 text-sm font-semibold text-slate-900 dark:text-white">2. Add the document</h2>
        <div className="mt-3 inline-flex rounded-xl bg-slate-100 p-1 dark:bg-slate-800" role="tablist">
          {[
            { k: "upload" as const, label: "Upload file", icon: Upload },
            { k: "paste" as const, label: "Paste text", icon: Type },
          ].map((t) => (
            <button
              key={t.k}
              role="tab"
              aria-selected={tab === t.k}
              onClick={() => setTab(t.k)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                tab === t.k ? "bg-white shadow-sm dark:bg-slate-900 dark:text-white" : "text-slate-500"
              }`}
            >
              <t.icon className="h-4 w-4" aria-hidden /> {t.label}
            </button>
          ))}
        </div>

        {tab === "upload" ? (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
            role="button"
            tabIndex={0}
            className={`mt-3 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-10 text-center transition ${
              drag ? "border-accent-500 bg-accent-50 dark:bg-accent-600/10" : "border-slate-300 hover:border-accent-500 dark:border-slate-700"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
            {file ? (
              <>
                <FileText className="h-10 w-10 text-accent-600" aria-hidden />
                <p className="mt-2 font-medium text-slate-900 dark:text-white">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB · click to change</p>
              </>
            ) : (
              <>
                <FileUp className="h-10 w-10 text-slate-400" aria-hidden />
                <p className="mt-2 font-medium text-slate-900 dark:text-white">Drop your file here, or click to browse</p>
                <p className="text-xs text-slate-500">PDF, DOCX or TXT · up to {MAX_MB} MB and 40 pages</p>
              </>
            )}
          </div>
        ) : (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={9}
            placeholder="Paste the full text of the agreement here…"
            className="mt-3 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 dark:border-slate-700 dark:bg-slate-950"
            aria-label="Agreement text"
          />
        )}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (optional)"
            className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 dark:border-slate-700 dark:bg-slate-950"
            aria-label="Document title"
            maxLength={200}
          />
          <button className="btn-primary sm:w-48" onClick={analyze} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
            {busy ? "Analysing…" : "Analyse document"}
          </button>
        </div>

        {busy && (
          <ol className="mt-6 grid gap-2 sm:grid-cols-4" aria-live="polite">
            {STEPS.map((s, i) => (
              <li
                key={s}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  i < step
                    ? "bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-300"
                    : i === step
                      ? "bg-accent-50 text-accent-700 dark:bg-accent-600/15 dark:text-accent-100"
                      : "bg-slate-100 text-slate-400 dark:bg-slate-800"
                }`}
              >
                {i < step ? <Check className="h-4 w-4" aria-hidden /> : i === step ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <span className="h-4 w-4" />}
                {s}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="fade-up mt-8" aria-label="Samples">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Or try a sample</h2>
        {samples.length === 0 ? (
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton h-20" />)}
          </div>
        ) : (
          GROUPS.map((g) => (
            <div key={g.kind} className="mt-4">
              <p className={`flex items-center gap-1.5 text-xs font-medium ${g.color}`}>
                <g.icon className="h-4 w-4" aria-hidden /> {g.label}
              </p>
              <div className="mt-2 grid gap-3 sm:grid-cols-3">
                {samples.filter((s) => s.kind === g.kind).map((s) => {
                  const Icon = TYPE_ICON[s.doc_type];
                  return (
                    <button
                      key={s.name}
                      disabled={busy || !s.available}
                      onClick={() => {
                        setDocType(s.doc_type);
                        run(() => api.analyzeSample(s.name));
                      }}
                      className="card flex items-start gap-3 p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md disabled:opacity-50"
                    >
                      <Icon className="mt-0.5 h-5 w-5 text-accent-600" aria-hidden />
                      <span>
                        <span className="block text-sm font-medium text-slate-900 dark:text-white">{s.title}</span>
                        <span className="block text-xs text-slate-500">{s.description}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </section>

      <p className="mt-10 text-center text-xs text-slate-500">
        Your document is analysed on this server only. ClauseGuard gives information, not legal advice.
      </p>
    </div>
  );
}
