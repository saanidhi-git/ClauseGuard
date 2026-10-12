import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, Beaker, Database, FlaskConical, Loader2, Table2 } from "lucide-react";
import { api, type ClassifyResult, type Insights as InsightsT } from "../api";
import { ConfidenceBar, RiskBadge } from "../components/Risk";
import { useToast } from "../components/Toast";

// colour follows the model, never its rank
const MODEL_COLOR: Record<string, string> = {
  "baseline-lr": "var(--series-1)",
  "baseline-nb": "var(--series-2)",
  "legal-bert": "var(--series-3)",
  hybrid: "var(--series-4)",
};
const MODEL_ORDER = ["baseline-lr", "baseline-nb", "legal-bert", "hybrid"];
const PIPELINE = ["Upload", "Extract text", "Segment clauses", "Preprocess", "Classify (14 labels)", "Risk score", "Explain + key facts", "RAG Q&A"];
const EXAMPLE = "If the Licensee vacates the flat before 6 months, the entire security deposit of Rs. 50,000 shall stand forfeited.";
const pct = (v: number) => `${(v * 100).toFixed(1)}`;

export default function Insights() {
  const toast = useToast();
  const [data, setData] = useState<InsightsT | null>(null);
  const [dataset, setDataset] = useState("unfair_tos_test");
  const [cmModel, setCmModel] = useState("baseline-lr");
  const [cmLabel, setCmLabel] = useState("limitation_of_liability");
  const [showTable, setShowTable] = useState(false);
  const [text, setText] = useState(EXAMPLE);
  const [result, setResult] = useState<ClassifyResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.insights().then((d) => {
      setData(d);
      if (d.model_used && d.model_used !== "keyword-fallback") setCmModel(d.model_used);
    }).catch((e) => toast(e.message, "error"));
  }, [toast]);

  const metrics = data?.metrics;
  const names = useMemo(() => Object.fromEntries((data?.labels ?? []).map((l) => [l.key, l.name])), [data]);
  const models = useMemo(
    () => MODEL_ORDER.filter((m) => metrics?.models[m]?.available && metrics.models[m].results[dataset]),
    [metrics, dataset],
  );

  const f1Rows = useMemo(() => {
    if (!metrics) return [];
    const first = models[0] && metrics.models[models[0]].results[dataset];
    if (!first) return [];
    return Object.keys(first.per_label)
      .filter((l) => first.per_label[l].support > 0)
      .map((l) => {
        const row: Record<string, string | number> = { label: names[l] ?? l };
        models.forEach((m) => (row[m] = +(metrics.models[m].results[dataset].per_label[l].f1 * 100).toFixed(1)));
        return row;
      });
  }, [metrics, models, dataset, names]);

  const classify = async () => {
    if (text.trim().length < 3) return;
    setBusy(true);
    try {
      setResult(await api.classify(text));
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  };

  const cm = metrics?.models[cmModel]?.results[dataset]?.per_label[cmLabel];
  const cmMax = cm ? Math.max(cm.tp, cm.fp, cm.fn, cm.tn, 1) : 1;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Model Insights</h1>
        {data?.is_baseline && (
          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
            baseline model
          </span>
        )}
        {data && <span className="text-sm text-slate-500">Model in use: <b>{data.model_used}</b></span>}
      </div>
      <p className="mt-1 text-sm text-slate-500">For evaluators: how the classifier was trained and how well it does. All numbers are computed by training/evaluate.py.</p>

      <section className="card mt-6 p-5" aria-label="Pipeline">
        <h2 className="font-semibold text-slate-900 dark:text-white">Pipeline</h2>
        <ol className="mt-4 flex flex-wrap items-center gap-2">
          {PIPELINE.map((p, i) => (
            <li key={p} className="flex items-center gap-2">
              <span className="rounded-lg border border-accent-100 bg-accent-50 px-3 py-1.5 text-sm font-medium text-accent-700 dark:border-slate-700 dark:bg-slate-800 dark:text-accent-100">
                {p}
              </span>
              {i < PIPELINE.length - 1 && <ArrowRight className="h-4 w-4 text-slate-400" aria-hidden />}
            </li>
          ))}
        </ol>
      </section>

      {!data && <div className="skeleton mt-6 h-72" />}
      {data && !metrics && (
        <div className="card mt-6 p-8 text-center text-sm text-slate-500">
          No metrics yet. Run <code>python training/evaluate.py</code> to compute them.
        </div>
      )}

      {metrics && (
        <>
          <div className="mt-6 flex flex-wrap items-center gap-2" role="group" aria-label="Test set">
            <span className="text-sm text-slate-500">Test set:</span>
            {[
              ["unfair_tos_test", "UNFAIR-ToS test"],
              ["clauseguard_in_test", "ClauseGuard-IN test"],
            ].map(([k, n]) => (
              <button
                key={k}
                onClick={() => setDataset(k)}
                aria-pressed={dataset === k}
                className={`rounded-full border px-3 py-1 text-sm ${
                  dataset === k ? "border-accent-600 bg-accent-600 text-white" : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900"
                }`}
              >
                {n}
              </button>
            ))}
          </div>

          <section className="card mt-4 overflow-x-auto p-5" aria-label="Model comparison">
            <h2 className="font-semibold text-slate-900 dark:text-white">Model comparison (%)</h2>
            <table className="mt-3 w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500 dark:border-slate-800">
                  <th className="py-2 font-medium">Model</th>
                  {["Micro P", "Micro R", "Micro F1", "Macro P", "Macro R", "Macro F1"].map((h) => (
                    <th key={h} className="py-2 text-right font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MODEL_ORDER.map((m) => {
                  const info = metrics.models[m];
                  const r = info?.results[dataset];
                  return (
                    <tr key={m} className="border-b border-slate-100 last:border-0 dark:border-slate-800">
                      <td className="py-2.5">
                        <span className="mr-2 inline-block h-2.5 w-2.5 rounded-sm" style={{ background: MODEL_COLOR[m] }} aria-hidden />
                        {info?.display_name ?? m}
                        {m === data?.model_used && <span className="ml-2 text-xs text-accent-600">(in use)</span>}
                      </td>
                      {r ? (
                        [r.micro_precision, r.micro_recall, r.micro_f1, r.macro_precision, r.macro_recall, r.macro_f1].map((v, i) => (
                          <td key={i} className={`py-2.5 text-right tabular-nums ${i === 2 || i === 5 ? "font-semibold text-slate-900 dark:text-white" : ""}`}>
                            {pct(v)}
                          </td>
                        ))
                      ) : (
                        <td colSpan={6} className="py-2.5 text-right text-slate-400">not trained yet</td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>

          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <section className="card p-5 lg:col-span-2" aria-label="Per-label F1">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-900 dark:text-white">Per-label F1 (%)</h2>
                <button className="btn-ghost px-2.5 py-1.5 text-xs" onClick={() => setShowTable(!showTable)}>
                  <Table2 className="h-3.5 w-3.5" aria-hidden /> {showTable ? "Chart" : "Table"}
                </button>
              </div>
              {showTable ? (
                <table className="mt-3 w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="py-1.5 font-medium">Label</th>
                      {models.map((m) => <th key={m} className="py-1.5 text-right font-medium">{metrics.models[m].display_name}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {f1Rows.map((r) => (
                      <tr key={r.label as string} className="border-t border-slate-100 dark:border-slate-800">
                        <td className="py-1.5">{r.label}</td>
                        {models.map((m) => <td key={m} className="py-1.5 text-right tabular-nums">{r[m]}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="mt-3" style={{ height: Math.max(260, f1Rows.length * 44) }}>
                  <ResponsiveContainer>
                    <BarChart data={f1Rows} layout="vertical" margin={{ left: 8, right: 16 }} barGap={2} barCategoryGap="22%">
                      <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
                      <XAxis type="number" domain={[0, 100]} tick={{ fill: "var(--chart-text)", fontSize: 12 }} stroke="var(--chart-grid)" />
                      <YAxis type="category" dataKey="label" width={150} tick={{ fill: "var(--chart-text)", fontSize: 12 }} stroke="var(--chart-grid)" />
                      <Tooltip
                        cursor={{ fill: "rgba(148,163,184,0.12)" }}
                        contentStyle={{ borderRadius: 12, fontSize: 12, background: "var(--tooltip-bg, #fff)", color: "#0f172a" }}
                        formatter={(v: number, k: string) => [`${v}%`, metrics.models[k]?.display_name ?? k]}
                      />
                      <Legend formatter={(k: string) => <span style={{ color: "var(--chart-text)" }}>{metrics.models[k]?.display_name ?? k}</span>} />
                      {models.map((m) => (
                        <Bar key={m} dataKey={m} fill={MODEL_COLOR[m]} radius={[0, 4, 4, 0]} maxBarSize={12} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </section>

            <section className="card p-5" aria-label="Confusion matrix">
              <h2 className="font-semibold text-slate-900 dark:text-white">Confusion matrix</h2>
              <div className="mt-3 grid gap-2">
                <select value={cmModel} onChange={(e) => setCmModel(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950" aria-label="Model">
                  {models.map((m) => <option key={m} value={m}>{metrics.models[m].display_name}</option>)}
                </select>
                <select value={cmLabel} onChange={(e) => setCmLabel(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950" aria-label="Label">
                  {metrics.labels.map((l) => <option key={l} value={l}>{names[l] ?? l}</option>)}
                </select>
              </div>
              {cm ? (
                <div className="mt-4">
                  <div className="grid grid-cols-[auto_1fr_1fr] gap-1.5 text-center text-xs">
                    <span />
                    <span className="text-slate-500">Pred. no</span>
                    <span className="text-slate-500">Pred. yes</span>
                    {[
                      ["Actual no", cm.tn, cm.fp, "TN", "FP"],
                      ["Actual yes", cm.fn, cm.tp, "FN", "TP"],
                    ].map(([name, a, b, la, lb]) => (
                      <Row key={name as string} name={name as string} cells={[[a as number, la as string], [b as number, lb as string]]} max={cmMax} />
                    ))}
                  </div>
                  <p className="mt-3 text-xs text-slate-500">
                    P {pct(cm.precision)} · R {pct(cm.recall)} · F1 {pct(cm.f1)} · support {cm.support}
                  </p>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">Not available for this model and test set.</p>
              )}
            </section>
          </div>

          <section className="mt-4 grid gap-4 md:grid-cols-2" aria-label="Datasets">
            {Object.entries(metrics.datasets).map(([k, d]) => (
              <div key={k} className="card p-5">
                <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
                  <Database className="h-4 w-4 text-accent-600" aria-hidden /> {d.name}
                </h2>
                <p className="mt-1 text-sm text-slate-500">{d.description}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {Object.entries(d.split_sizes).map(([s, n]) => (
                    <span key={s} className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs dark:bg-slate-800">
                      {s}: <b className="tabular-nums">{n}</b>
                    </span>
                  ))}
                </div>
                <table className="mt-3 w-full text-xs">
                  <tbody>
                    {Object.entries(d.label_counts).map(([l, n]) => (
                      <tr key={l} className="border-t border-slate-100 dark:border-slate-800">
                        <td className="py-1">{names[l] ?? l}</td>
                        <td className="py-1 text-right tabular-nums">{n}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </section>
        </>
      )}

      <section className="card mt-6 p-5" aria-label="Test a single clause">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <FlaskConical className="h-4 w-4 text-accent-600" aria-hidden /> Test a single clause
        </h2>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          maxLength={5000}
          className="mt-3 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 dark:border-slate-700 dark:bg-slate-950"
          aria-label="Clause text"
        />
        <button className="btn-primary mt-2" onClick={classify} disabled={busy}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Beaker className="h-4 w-4" aria-hidden />} Classify
        </button>

        {result && (
          <div className="fade-up mt-5 grid gap-5 lg:grid-cols-2">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <RiskBadge level={result.risk_level} />
                <span className="text-xs text-slate-500">using {result.model_used}</span>
              </div>
              {result.explanation.explanation && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{result.explanation.explanation}</p>}
              <ProbTable result={result} names={names} />
            </div>
            <Preprocessing p={result.preprocessing} />
          </div>
        )}
      </section>
    </div>
  );
}

function Row({ name, cells, max }: { name: string; cells: [number, string][]; max: number }) {
  return (
    <>
      <span className="self-center pr-1 text-right text-slate-500">{name}</span>
      {cells.map(([v, l]) => {
        const strength = v / max;
        return (
          <div
            key={l}
            className="rounded-lg p-3"
            style={{ background: `rgba(79,70,229,${0.08 + strength * 0.75})`, color: strength > 0.5 ? "#fff" : undefined }}
            title={`${l}: ${v}`}
          >
            <p className="text-lg font-bold tabular-nums">{v}</p>
            <p className="opacity-80">{l}</p>
          </div>
        );
      })}
    </>
  );
}

function ProbTable({ result, names }: { result: ClassifyResult; names: Record<string, string> }) {
  const [all, setAll] = useState(false);
  const models = MODEL_ORDER.filter((m) => result.models[m]);
  const labels = Object.keys(result.models[models[0]]?.probs ?? {})
    .map((l) => ({ l, max: Math.max(...models.map((m) => result.models[m].probs[l])) }))
    .sort((a, b) => b.max - a.max)
    .filter((x, i) => all || x.max >= 0.1 || i < 3);
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[420px] text-xs">
        <thead>
          <tr className="text-left text-slate-500">
            <th className="py-1.5 font-medium">Label</th>
            {models.map((m) => <th key={m} className="py-1.5 font-medium">{m}</th>)}
          </tr>
        </thead>
        <tbody>
          {labels.map(({ l }) => (
            <tr key={l} className="border-t border-slate-100 dark:border-slate-800">
              <td className="py-1.5 pr-2">{names[l] ?? l}</td>
              {models.map((m) => (
                <td key={m} className="py-1.5 pr-2">
                  <ConfidenceBar value={result.models[m].probs[l]} color={MODEL_COLOR[m]} />
                  {result.models[m].labels.includes(l) && <span className="text-[10px] font-semibold text-accent-600">predicted</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <button className="mt-2 text-xs text-accent-600 hover:underline" onClick={() => setAll(!all)}>
        {all ? "Show top labels only" : "Show all 14 labels"}
      </button>
    </div>
  );
}

function Preprocessing({ p }: { p: ClassifyResult["preprocessing"] }) {
  const rows: [string, string[]][] = [
    ["Tokens", p.tokens],
    ["Without stopwords", p.without_stopwords],
    ["Lemmas", p.lemmas],
    ["POS tags", p.pos.map((t) => `${t.text}/${t.pos}`)],
    ["Entities", p.entities.map((e) => `${e.text} · ${e.label}`)],
  ];
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Preprocessing</h3>
      <div className="mt-2 space-y-3">
        {rows.map(([name, items]) => (
          <div key={name}>
            <p className="text-xs text-slate-500">{name} ({items.length})</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {items.length === 0 && <span className="text-xs text-slate-400">none</span>}
              {items.slice(0, 60).map((t, i) => (
                <span key={i} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] dark:bg-slate-800">{t}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
