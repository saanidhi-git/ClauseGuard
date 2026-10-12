import { HelpCircle, Lightbulb, MessageSquareQuote, X } from "lucide-react";
import type { Clause } from "../api";
import { ConfidenceBar, LEVEL_STYLE, RiskBadge } from "./Risk";

export default function ClausePanel({ clause, onClose }: { clause: Clause; onClose: () => void }) {
  const exp = clause.explanation;
  const color = LEVEL_STYLE[clause.risk_level].bar;
  return (
    <>
      <div className="fixed inset-0 z-40 bg-slate-900/30 lg:hidden" onClick={onClose} aria-hidden />
      <aside
        className="slide-in fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900"
        aria-label={`Clause ${clause.number} details`}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div>
            <p className="text-xs text-slate-500">Page {clause.page}</p>
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Clause {clause.number}
              {clause.heading && <span className="font-normal text-slate-500"> · {clause.heading}</span>}
            </h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close panel">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
          <div className="flex flex-wrap items-center gap-2">
            <RiskBadge level={clause.risk_level} />
            {exp.categories?.map((c) => (
              <span key={c.key} className="rounded-full border border-slate-200 px-2.5 py-1 text-xs font-medium dark:border-slate-700">
                {c.name} · {c.severity}
              </span>
            ))}
          </div>

          <blockquote className="rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-700 dark:bg-slate-950 dark:text-slate-300">
            {clause.text}
          </blockquote>

          {clause.risk_level === "Safe" ? (
            <p className="text-sm text-slate-600 dark:text-slate-400">
              No risky pattern was found in this clause. It still helps to read it carefully.
            </p>
          ) : (
            <>
              <Section icon={MessageSquareQuote} title="What it means" text={exp.explanation} />
              <Section icon={Lightbulb} title="Why it matters" text={exp.why} />
              <Section icon={HelpCircle} title="Ask before signing" text={exp.ask} />
              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-white">Model confidence</h3>
                <div className="space-y-2">
                  {exp.categories.map((c) => (
                    <div key={c.key}>
                      <p className="mb-1 text-xs text-slate-500">{c.name}</p>
                      <ConfidenceBar value={c.probability} color={color} />
                    </div>
                  ))}
                </div>
              </div>
              {exp.source === "llm" && <p className="text-xs text-slate-400">Explanation rewritten by an AI model from the clause text.</p>}
            </>
          )}
        </div>
        <p className="border-t border-slate-200 px-5 py-3 text-xs text-slate-500 dark:border-slate-800">
          ClauseGuard gives information, not legal advice.
        </p>
      </aside>
    </>
  );
}

function Section({ icon: Icon, title, text }: { icon: typeof X; title: string; text: string }) {
  return (
    <div>
      <h3 className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-white">
        <Icon className="h-4 w-4 text-accent-600" aria-hidden /> {title}
      </h3>
      <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">{text}</p>
    </div>
  );
}
