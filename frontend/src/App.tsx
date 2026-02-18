import { useState, useCallback } from "react";
import { chat, retrieve, uploadDocuments, openclawSend, generateDocument, getEvalReport, runEval, getSystemHealth } from "./api";
import type { ChatResponse, RetrieveResponse, DocumentsResponse, EvalReport, SystemHealthResponse } from "./api";
import "./App.css";
import voiceflipLogo from "./assets/images/voiceflip-logo.png";

type TabId = "chat" | "upload" | "retrieve" | "openclaw" | "eval";

type Message = { role: "user" | "assistant"; content: string };

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("chat");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [files, setFiles] = useState<File[]>([]);
  const [uploadResult, setUploadResult] = useState<DocumentsResponse | null>(null);

  // Retrieve state
  const [retrieveQuery, setRetrieveQuery] = useState("");
  const [retrieveTechnique, setRetrieveTechnique] = useState<"top_k" | "mmr">("top_k");
  const [retrieveResult, setRetrieveResult] = useState<RetrieveResponse | null>(null);

  // OpenClaw state
  const [openclawMessage, setOpenclawMessage] = useState("");
  const [openclawSent, setOpenclawSent] = useState<string | null>(null);
  // Generate document from research text (title, content, format)
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [docFormat, setDocFormat] = useState<"docx" | "pdf">("docx");
  const [docGenerated, setDocGenerated] = useState(false);

  // System Metrics Dashboard (RAGAS + health)
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [evalReport, setEvalReport] = useState<EvalReport | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalRunLoading, setEvalRunLoading] = useState(false);
  const [evalFile, setEvalFile] = useState<File | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const formatMetric = (v: number | string | undefined): string => {
    if (v == null) return "—";
    if (typeof v === "number") return v.toFixed(4);
    return String(v);
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setError(null);
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res: ChatResponse = await chat(msg, sessionId ?? undefined);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
      setMessages((m) => m.slice(0, -1)); // remove user message on error
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = retrieveQuery.trim();
    if (!q || loading) return;
    setError(null);
    setLoading(true);
    try {
      const res = await retrieve(q, retrieveTechnique);
      setRetrieveResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retrieval failed");
      setRetrieveResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0 || loading) return;
    setError(null);
    setLoading(true);
    try {
      const res = await uploadDocuments(files);
      setUploadResult(res);
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    const valid = selected.filter((f) =>
      [".docx", ".html", ".htm"].some((ext) =>
        f.name.toLowerCase().endsWith(ext)
      )
    );
    setFiles((prev) => [...prev, ...valid]);
    setUploadResult(null);
    e.target.value = "";
  };

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleOpenClawSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const msg = openclawMessage.trim();
    if (!msg || loading) return;
    setError(null);
    setOpenclawSent(null);
    setLoading(true);
    try {
      await openclawSend(msg);
      setOpenclawSent(msg);
      setOpenclawMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send to OpenClaw failed");
    } finally {
      setLoading(false);
    }
  };

  const loadSystemHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      const data = await getSystemHealth();
      setSystemHealth(data);
    } catch {
      setSystemHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  const loadEvalReport = useCallback(async () => {
    setError(null);
    setEvalLoading(true);
    try {
      const report = await getEvalReport();
      setEvalReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report");
      setEvalReport(null);
    } finally {
      setEvalLoading(false);
    }
  }, []);

  const handleRunEval = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setEvalRunLoading(true);
    try {
      const report = await runEval(evalFile ?? undefined);
      setEvalReport(report);
      setEvalFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setEvalRunLoading(false);
    }
  };

  const handleGenerateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    const title = docTitle.trim() || "Research Document";
    const content = docContent.trim();
    if (!content || loading) return;
    setError(null);
    setDocGenerated(false);
    setLoading(true);
    try {
      await generateDocument(title, content, docFormat);
      setDocGenerated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generate document failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <img src={voiceflipLogo} alt="Voiceflip" className="header-logo" />
        <h1 className="header-title">US Housing strategies chatbot</h1>
        <p className="subtitle">Chat, Upload Documents, Retrieve</p>
        <nav className="tabs">
          <button
            className={activeTab === "chat" ? "active" : ""}
            onClick={() => {
              setActiveTab("chat");
              clearError();
            }}
          >
            Chat
          </button>
          <button
            className={activeTab === "upload" ? "active" : ""}
            onClick={() => {
              setActiveTab("upload");
              clearError();
            }}
          >
            Upload Documents
          </button>
          <button
            className={activeTab === "retrieve" ? "active" : ""}
            onClick={() => {
              setActiveTab("retrieve");
              clearError();
            }}
          >
            Retrieval
          </button>
          <button
            className={activeTab === "openclaw" ? "active" : ""}
            onClick={() => {
              setActiveTab("openclaw");
              clearError();
            }}
          >
            OpenClaw
          </button>
          <button
            className={activeTab === "eval" ? "active" : ""}
            onClick={() => {
              setActiveTab("eval");
              clearError();
              if (activeTab !== "eval") {
                loadSystemHealth();
                loadEvalReport();
              }
            }}
          >
            System Metrics Dashboard
          </button>
        </nav>
      </header>

      {error && (
        <div className="banner error" role="alert">
          {error}
          <button type="button" onClick={clearError} aria-label="Dismiss">
            ×
          </button>
        </div>
      )}

      <main className="main">
        {activeTab === "chat" && (
          <section className="panel chat-panel">
            <div className="messages">
              {messages.length === 0 && (
                <p className="placeholder">
                  Start a conversation. The agent uses RAG, relevance checks, and web search fallback.
                </p>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>
                  <strong>{m.role === "user" ? "You" : "Assistant"}</strong>
                  <div>{m.content}</div>
                </div>
              ))}
              {loading && (
                <div className="message assistant loading">
                  <strong>Assistant</strong>
                  <div>Thinking…</div>
                </div>
              )}
            </div>
            <form onSubmit={handleChatSubmit} className="form">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message…"
                disabled={loading}
                autoComplete="off"
              />
              <button type="submit" disabled={loading || !input.trim()}>
                Send
              </button>
            </form>
          </section>
        )}

        {activeTab === "upload" && (
          <section className="panel upload-panel">
            <p className="hint">
              Supported formats: DOCX, HTML. Files are chunked and added to the vector store.
            </p>
            <form onSubmit={handleUploadSubmit} className="form upload-form">
              <label className="file-label">
                <input
                  type="file"
                  multiple
                  accept=".docx,.html,.htm"
                  onChange={handleFileChange}
                />
                Choose files
              </label>
              {files.length > 0 && (
                <ul className="file-list">
                  {files.map((f, i) => (
                    <li key={i}>
                      {f.name}{" "}
                      <button
                        type="button"
                        onClick={() => removeFile(i)}
                        aria-label={`Remove ${f.name}`}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <button
                type="submit"
                disabled={loading || files.length === 0}
              >
                {loading ? "Uploading…" : "Upload"}
              </button>
            </form>
            {uploadResult && (
              <div className="result-box">
                <h3>Result</h3>
                <p>Ingested: {uploadResult.ingested} | Chunks: {uploadResult.chunks}</p>
                {uploadResult.files.length > 0 && (
                  <p>Files: {uploadResult.files.join(", ")}</p>
                )}
                {uploadResult.errors.length > 0 && (
                  <ul className="errors">
                    {uploadResult.errors.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </section>
        )}

        {activeTab === "retrieve" && (
          <section className="panel retrieve-panel">
            <p className="hint">
              Search the vector store with top_k or MMR. Results show content and metadata.
            </p>
            <form onSubmit={handleRetrieveSubmit} className="form">
              <input
                type="text"
                value={retrieveQuery}
                onChange={(e) => setRetrieveQuery(e.target.value)}
                placeholder="Enter search query…"
                disabled={loading}
                autoComplete="off"
              />
              <select
                value={retrieveTechnique}
                onChange={(e) =>
                  setRetrieveTechnique(e.target.value as "top_k" | "mmr")
                }
                disabled={loading}
              >
                <option value="top_k">top_k</option>
                <option value="mmr">MMR</option>
              </select>
              <button
                type="submit"
                disabled={loading || !retrieveQuery.trim()}
              >
                {loading ? "Searching…" : "Retrieve"}
              </button>
            </form>
            {retrieveResult && (
              <div className="result-box retrieve-results">
                <h3>
                  {retrieveResult.count} document(s) for &quot;{retrieveResult.query}&quot; ({retrieveResult.technique})
                </h3>
                <ul className="doc-list">
                  {retrieveResult.documents.map((d, i) => (
                    <li key={i} className="doc-item">
                      <details>
                        <summary>Document {i + 1}</summary>
                        <pre>{d.content}</pre>
                        {Object.keys(d.metadata).length > 0 && (
                          <pre className="meta">{JSON.stringify(d.metadata, null, 2)}</pre>
                        )}
                      </details>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {activeTab === "openclaw" && (
          <section className="panel openclaw-panel">
            <p className="hint">
              <strong>Flow:</strong> Ask OpenClaw for US housing research (e.g. &quot;Search for information about first-time home buyer programs in the US&quot;). Paste the reply below, generate a PDF or DOCX, download it, then add it to the RAG via the Upload tab.
            </p>
            <form onSubmit={handleOpenClawSend} className="form">
              <input
                type="text"
                value={openclawMessage}
                onChange={(e) => setOpenclawMessage(e.target.value)}
                placeholder="e.g. Search for US housing tax credits and first-time buyer programs…"
                disabled={loading}
                autoComplete="off"
              />
              <button type="submit" disabled={loading || !openclawMessage.trim()}>
                {loading ? "Sending…" : "Send to OpenClaw"}
              </button>
            </form>
            {openclawSent && (
              <div className="result-box success">
                Message sent. Check OpenClaw for the reply, then paste it below to generate a document.
              </div>
            )}

            <h3 className="section-title">Generate document from research text</h3>
            <p className="hint">Paste the text from OpenClaw (or any source), add a title, and download as PDF or DOCX. Then use the Upload tab to add it to the RAG context.</p>
            <form onSubmit={handleGenerateDocument} className="form generate-doc-form">
              <input
                type="text"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                placeholder="Document title (e.g. US Housing Programs Summary)"
                disabled={loading}
                autoComplete="off"
              />
              <textarea
                value={docContent}
                onChange={(e) => setDocContent(e.target.value)}
                placeholder="Paste research text here…"
                rows={8}
                disabled={loading}
              />
              <div className="form-row">
                <label>
                  Format:{" "}
                  <select
                    value={docFormat}
                    onChange={(e) => setDocFormat(e.target.value as "docx" | "pdf")}
                    disabled={loading}
                  >
                    <option value="docx">DOCX</option>
                    <option value="pdf">PDF</option>
                  </select>
                </label>
                <button type="submit" disabled={loading || !docContent.trim()}>
                  {loading ? "Generating…" : "Generate and download"}
                </button>
              </div>
            </form>
            {docGenerated && (
              <div className="result-box success">
                Document downloaded. To add it to the RAG context, go to <button type="button" className="link-button" onClick={() => { setActiveTab("upload"); clearError(); }}>Upload Documents</button> and upload the file (DOCX is supported for ingestion).
              </div>
            )}
          </section>
        )}

        {activeTab === "eval" && (
          <section className="panel eval-panel">
            <h2 className="panel-title">System Metrics Dashboard</h2>

            <h3 className="system-metrics-section-title">Service health</h3>
            <div className="health-actions">
              <button
                type="button"
                onClick={loadSystemHealth}
                disabled={healthLoading}
              >
                {healthLoading ? "Checking…" : "Refresh health"}
              </button>
            </div>
            {healthLoading && !systemHealth ? (
              <p className="hint">Checking services…</p>
            ) : systemHealth ? (
              <div className="health-services">
                {(["api", "vectordb", "openclaw_gateway"] as const).map((key) => {
                  const s = systemHealth.services[key];
                  const label = key === "api" ? "API" : key === "vectordb" ? "Vector DB (Qdrant)" : "OpenClaw Gateway";
                  const status = s.status === "ok" ? "ok" : s.status === "unconfigured" ? "unconfigured" : "error";
                  const message = "message" in s ? s.message : null;
                  return (
                    <div key={key} className={`health-card health-card--${status}`}>
                      <span className="health-card__label">{label}</span>
                      <span className="health-card__status">{status}</span>
                      {message && <span className="health-card__message">{message}</span>}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="hint">Could not load service health. Ensure the API is running.</p>
            )}

            <h3 className="system-metrics-section-title">RAGAS evaluation metrics</h3>
            <p className="hint">
              Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall, Hallucination Score, Latency. Use <strong>question_list.pdf</strong> (or upload one) with ≥15 questions.
            </p>
            <div className="eval-actions">
              <button
                type="button"
                onClick={loadEvalReport}
                disabled={evalLoading}
              >
                {evalLoading ? "Loading…" : "Load last report"}
              </button>
              <form onSubmit={handleRunEval} className="eval-run-form">
                <label className="file-label">
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc"
                    onChange={(e) => setEvalFile(e.target.files?.[0] ?? null)}
                  />
                  {evalFile ? evalFile.name : "Choose question list (PDF/DOCX)"}
                </label>
                <button type="submit" disabled={evalRunLoading}>
                  {evalRunLoading ? "Running evaluation…" : "Run evaluation"}
                </button>
              </form>
            </div>
            {evalReport && (
              <div className="eval-dashboard">
                <div className="eval-summary">
                  <strong>Questions used:</strong> {evalReport.num_questions}
                </div>
                <div className="eval-metrics">
                  <div className="metric-card">
                    <span className="metric-label">Faithfulness</span>
                    <span className="metric-value">{formatMetric(evalReport.metrics.faithfulness)}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Answer Relevancy</span>
                    <span className="metric-value">{formatMetric(evalReport.metrics.answer_relevancy)}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Context Precision</span>
                    <span className="metric-value">{formatMetric(evalReport.metrics.context_precision)}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Context Recall</span>
                    <span className="metric-value">{formatMetric(evalReport.metrics.context_recall)}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Hallucination Score</span>
                    <span className="metric-value">{formatMetric(evalReport.metrics.hallucination_score)}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Latency (avg)</span>
                    <span className="metric-value">{evalReport.metrics.latency_avg_seconds != null ? `${evalReport.metrics.latency_avg_seconds}s` : "—"}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Latency (max)</span>
                    <span className="metric-value">{evalReport.metrics.latency_max_seconds != null ? `${evalReport.metrics.latency_max_seconds}s` : "—"}</span>
                  </div>
                </div>
              </div>
            )}
            {activeTab === "eval" && !evalReport && !evalLoading && !evalRunLoading && (
              <p className="hint">Load a saved report or run an evaluation to see metrics.</p>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
          OpenAPI docs
        </a>
      </footer>
    </div>
  );
}

export default App;
