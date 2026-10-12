import { useEffect, useRef, useState, type FormEvent } from "react";
import { Loader2, Send, Sparkles, X } from "lucide-react";
import { api, type ChatMsg, type Clause, type DocType } from "../api";

const SUGGESTED: Record<DocType, string[]> = {
  rental: ["Can I leave before the lock-in ends?", "When will I get my deposit back?", "How much notice must I give?", "Can the rent be increased?"],
  offer_letter: ["What happens if I resign within 2 years?", "What is the notice period?", "Can I join a competitor later?", "Can they change my location?"],
  tos: ["Can they delete my account?", "Who do they share my data with?", "Where do I file a complaint?", "Can they change the terms?"],
};

interface Props {
  docId: number;
  docType: DocType;
  clauses: Clause[];
  onClose: () => void;
  onCite: (clauseId: number) => void;
}

export default function ChatDrawer({ docId, docType, clauses, onClose, onCite }: Props) {
  const [msgs, setMsgs] = useState<ChatMsg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const byId = Object.fromEntries(clauses.map((c) => [c.id, c]));

  useEffect(() => {
    api.chat(docId).then(setMsgs).catch(() => setMsgs([]));
  }, [docId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  const ask = async (question: string) => {
    const text = question.trim();
    if (text.length < 2 || busy) return;
    setErr("");
    setQ("");
    setMsgs((m) => [...m, { role: "user", content: text, cited_clause_ids: [] }]);
    setBusy(true);
    try {
      const r = await api.ask(docId, text);
      setMsgs((m) => [...m, { role: "assistant", content: r.answer, cited_clause_ids: r.cited_clause_ids }]);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    ask(q);
  };

  return (
    <aside
      className="slide-in fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900"
      aria-label="Ask ClauseGuard"
    >
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Sparkles className="h-5 w-5 text-accent-600" aria-hidden /> Ask ClauseGuard
        </h2>
        <button onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close chat">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5" aria-live="polite">
        {msgs.length === 0 && (
          <div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Ask anything about this document. Answers come only from its clauses, with clause numbers you can click.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              {SUGGESTED[docType].map((s) => (
                <button key={s} onClick={() => ask(s)} className="btn-ghost justify-start text-left">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-accent-600 text-white"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
              }`}
            >
              <p className="whitespace-pre-line leading-relaxed">{m.content}</p>
              {m.role === "assistant" && m.cited_clause_ids.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.cited_clause_ids.map((id) => (
                    <button
                      key={id}
                      onClick={() => onCite(id)}
                      className="rounded-full bg-white px-2.5 py-0.5 text-xs font-medium text-accent-700 ring-1 ring-accent-100 hover:bg-accent-50 dark:bg-slate-900 dark:text-accent-100 dark:ring-slate-700"
                    >
                      Clause {byId[id]?.number ?? id}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> Searching the clauses…
          </div>
        )}
        {err && <p className="text-sm text-red-600">{err}</p>}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-slate-200 p-4 dark:border-slate-800">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. Can I leave before 6 months?"
          maxLength={500}
          className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 dark:border-slate-700 dark:bg-slate-950"
          aria-label="Your question"
        />
        <button className="btn-primary px-3" disabled={busy || q.trim().length < 2} aria-label="Send">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </aside>
  );
}
