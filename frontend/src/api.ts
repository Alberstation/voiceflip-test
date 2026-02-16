/**
 * API client for RAG AI Engineer backend.
 * Uses VITE_API_URL or falls back to http://localhost:8000 when running standalone.
 */

const API_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: T;
  try {
    data = text ? JSON.parse(text) : ({} as T);
  } catch {
    throw new Error(text || res.statusText);
  }
  if (!res.ok) {
    const msg = (data as { detail?: string | { msg?: string }[] })?.detail;
    const err = Array.isArray(msg)
      ? msg.map((m) => m?.msg ?? m).join(", ")
      : typeof msg === "string"
        ? msg
        : res.statusText;
    throw new Error(err || `HTTP ${res.status}`);
  }
  return data;
}

export type ChatResponse = { answer: string; session_id: string };
export type QueryResponse = {
  answer: string;
  citations: { content?: string; metadata?: Record<string, unknown> }[];
  below_threshold: boolean;
};
export type RetrieveDoc = { content: string; metadata: Record<string, unknown> };
export type RetrieveResponse = {
  query: string;
  technique: string;
  count: number;
  documents: RetrieveDoc[];
};
export type DocumentsResponse = {
  ingested: number;
  chunks: number;
  files: string[];
  errors: string[];
};

export async function chat(message: string, sessionId?: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId ?? null }),
  });
  return handleResponse<ChatResponse>(res);
}

export async function query(
  question: string,
  retrievalTechnique: "top_k" | "mmr"
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      retrieval_technique: retrievalTechnique,
    }),
  });
  return handleResponse<QueryResponse>(res);
}

export async function retrieve(
  query: string,
  technique: "top_k" | "mmr"
): Promise<RetrieveResponse> {
  const res = await fetch(`${API_BASE}/retrieve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, technique }),
  });
  return handleResponse<RetrieveResponse>(res);
}

export async function uploadDocuments(
  files: File[]
): Promise<DocumentsResponse> {
  const formData = new FormData();
  for (const f of files) {
    formData.append("files", f);
  }
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentsResponse>(res);
}

export async function health(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse<{ status: string }>(res);
}
