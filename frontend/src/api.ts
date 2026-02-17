/**
 * API client for Voiceflip AI Engineer backend.
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

export type OpenClawSendResponse = { ok: boolean; result?: unknown; error?: string };

export async function openclawSend(message: string): Promise<OpenClawSendResponse> {
  const res = await fetch(`${API_BASE}/openclaw/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return handleResponse<OpenClawSendResponse>(res);
}

/** Generate DOCX or PDF from title + content; triggers browser download. */
export async function generateDocument(
  title: string,
  content: string,
  format: "docx" | "pdf"
): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content, format }),
  });
  if (!res.ok) {
    const text = await res.text();
    let msg: string;
    try {
      const j = JSON.parse(text);
      msg = j.detail ?? text;
    } catch {
      msg = text || res.statusText;
    }
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  const disposition = res.headers.get("Content-Disposition");
  const filename =
    disposition?.match(/filename="?([^";\n]+)"?/)?.[1]?.trim() ||
    `document.${format}`;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
