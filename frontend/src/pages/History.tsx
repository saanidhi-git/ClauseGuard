import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileClock, Loader2, Trash2 } from "lucide-react";
import { api, type DocSummary } from "../api";
import { RiskBadge, scoreLevel } from "../components/Risk";
import { useToast } from "../components/Toast";

export default function HistoryPage() {
  const toast = useToast();
  const [docs, setDocs] = useState<DocSummary[] | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  useEffect(() => {
    api.list().then(setDocs).catch((e) => {
      toast(e.message, "error");
      setDocs([]);
    });
  }, [toast]);

  const remove = async (d: DocSummary) => {
    if (!window.confirm(`Delete "${d.title}" and its chat history?`)) return;
    setDeleting(d.id);
    try {
      await api.remove(d.id);
      setDocs((all) => all?.filter((x) => x.id !== d.id) ?? null);
      toast("Document deleted.");
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">History</h1>
      <p className="text-sm text-slate-500">Documents you have analysed on this server.</p>

      <div className="mt-6 space-y-2.5">
        {docs === null && [0, 1, 2].map((i) => <div key={i} className="skeleton h-20" />)}
        {docs?.length === 0 && (
          <div className="card flex flex-col items-center p-12 text-center">
            <FileClock className="h-10 w-10 text-slate-400" aria-hidden />
            <p className="mt-3 font-medium text-slate-900 dark:text-white">No documents yet</p>
            <p className="text-sm text-slate-500">Analyse an agreement and it will show up here.</p>
            <Link to="/" className="btn-primary mt-5">Analyse a document</Link>
          </div>
        )}
        {docs?.map((d) => (
          <div key={d.id} className="card fade-up flex items-center gap-4 p-4">
            <Link to={`/report/${d.id}`} className="min-w-0 flex-1">
              <p className="truncate font-medium text-slate-900 hover:text-accent-600 dark:text-white">{d.title}</p>
              <p className="text-xs text-slate-500">
                {d.doc_type_name} · {new Date(d.created_at).toLocaleString()}
                {d.status !== "done" && ` · ${d.status}`}
              </p>
            </Link>
            <div className="hidden text-right sm:block">
              <p className="text-xl font-bold tabular-nums text-slate-900 dark:text-white">{d.score}</p>
              <p className="text-xs text-slate-500">score</p>
            </div>
            <RiskBadge level={scoreLevel(d.score)} small />
            <button
              onClick={() => remove(d)}
              disabled={deleting === d.id}
              className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
              aria-label={`Delete ${d.title}`}
            >
              {deleting === d.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
