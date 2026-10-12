// Small typed client for the ClauseGuard API

export type DocType = "rental" | "offer_letter" | "tos";
export type Level = "High" | "Medium" | "Low" | "Safe";

export interface Category {
  key: string;
  name: string;
  severity: string;
  probability: number;
}

export interface Explanation {
  categories: Category[];
  explanation: string;
  why: string;
  ask: string;
  source: string;
}

export interface Clause {
  id: number;
  number: string;
  heading: string;
  text: string;
  page: number;
  labels: string[];
  label_names: string[];
  probs: Record<string, number>;
  risk_level: Level;
  risk_score: number;
  explanation: Explanation;
}

export interface Fact {
  label: string;
  value: string | string[];
  clause_id: number;
}

export interface DocSummary {
  id: number;
  title: string;
  doc_type: DocType;
  doc_type_name: string;
  filename: string | null;
  created_at: string;
  score: number;
  verdict: string;
  status: "processing" | "done" | "error";
  level_counts: Record<Level, number>;
}

export interface DocDetail extends DocSummary {
  error: string | null;
  key_facts: Record<string, Fact>;
  summary: string[];
  model_used: string;
  page_count: number;
  clauses: Clause[];
  disclaimer: string;
}

export interface AskResult {
  answer: string;
  cited_clause_ids: number[];
  mode: "llm" | "retrieval";
  matches: { clause_id: number; number: string; score: number; highlight: string }[];
}

export interface ChatMsg {
  id?: number;
  role: "user" | "assistant";
  content: string;
  cited_clause_ids: number[];
}

export interface Sample {
  name: string;
  title: string;
  doc_type: DocType;
  description: string;
  available: boolean;
  kind: "risky" | "fair";
}

export interface Scores {
  micro_precision: number;
  micro_recall: number;
  micro_f1: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  per_label: Record<string, { precision: number; recall: number; f1: number; support: number; tp: number; fp: number; fn: number; tn: number }>;
}

export interface Metrics {
  generated_at: string;
  models: Record<string, { display_name: string; available: boolean; results: Record<string, Scores> }>;
  datasets: Record<string, { name: string; split_sizes: Record<string, number>; label_counts: Record<string, number>; description: string }>;
  labels: string[];
}

export interface Insights {
  metrics: Metrics | null;
  model_used: string;
  available_models: string[];
  is_baseline: boolean;
  labels: { key: string; name: string; severity: number; doc_types: string[] }[];
}

export interface ClassifyResult {
  models: Record<string, { probs: Record<string, number>; labels: string[] }>;
  model_used: string;
  risk_level: Level;
  risk_score: number;
  explanation: Explanation;
  preprocessing: {
    normalized: string[];
    tokens: string[];
    without_stopwords: string[];
    lemmas: string[];
    pos: { text: string; pos: string }[];
    entities: { text: string; label: string }[];
  };
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new Error("Can't reach the ClauseGuard server. Is the backend running?");
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
      else if (Array.isArray(body.detail)) msg = body.detail[0]?.msg ?? msg;
    } catch {
      /* not json */
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  uploadFile: (file: File, docType: DocType, title: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("doc_type", docType);
    fd.append("title", title);
    return request<{ document_id: number; status: string }>("/api/documents", { method: "POST", body: fd });
  },
  uploadText: (text: string, docType: DocType, title: string) =>
    request<{ document_id: number; status: string }>("/api/documents", json({ text, doc_type: docType, title })),
  list: () => request<DocSummary[]>("/api/documents"),
  get: (id: number) => request<DocDetail>(`/api/documents/${id}`),
  remove: (id: number) => request<{ ok: boolean }>(`/api/documents/${id}`, { method: "DELETE" }),
  ask: (id: number, question: string) => request<AskResult>(`/api/documents/${id}/ask`, json({ question })),
  chat: (id: number) => request<ChatMsg[]>(`/api/documents/${id}/chat`),
  samples: () => request<Sample[]>("/api/samples"),
  analyzeSample: (name: string) => request<{ document_id: number }>(`/api/samples/${name}/analyze`, { method: "POST" }),
  insights: () => request<Insights>("/api/insights"),
  classify: (text: string) => request<ClassifyResult>("/api/insights/classify", json({ text })),
  reportUrl: (id: number) => `/api/documents/${id}/report.pdf`,
};

export const DOC_TYPES: { key: DocType; name: string; hint: string }[] = [
  { key: "rental", name: "Rental agreement", hint: "Flat, PG or leave-and-licence" },
  { key: "offer_letter", name: "Job offer letter", hint: "Offer, appointment or bond" },
  { key: "tos", name: "Terms of Service", hint: "App terms or privacy policy" },
];

export const DOC_TYPE_NAME: Record<string, string> = Object.fromEntries(DOC_TYPES.map((d) => [d.key, d.name]));
