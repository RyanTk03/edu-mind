"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import type { QCM, QCMDifficulty } from "@/types";

const DIFFICULTY_LABELS: Record<QCMDifficulty, string> = {
  easy: "Facile",
  medium: "Intermédiaire",
  hard: "Difficile",
};

const DIFFICULTY_COLORS: Record<QCMDifficulty, string> = {
  easy: "#22c55e",
  medium: "#f59e0b",
  hard: "#ef4444",
};

const STATUS_LABELS: Record<string, string> = {
  generated: "En attente",
  submitted: "Soumis",
  evaluated: "Évalué",
};

const GRADE_COLORS: Record<string, string> = {
  A: "#22c55e",
  B: "#84cc16",
  C: "#f59e0b",
  D: "#f97316",
  F: "#ef4444",
};

export default function QCMListPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [qcms, setQcms] = useState<QCM[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showWorkflow, setShowWorkflow] = useState(false);

  // Generation form state
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState<QCMDifficulty>("medium");
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && sessionId) loadQCMs();
  }, [isAuthenticated, sessionId]);

  const loadQCMs = async () => {
    try {
      const data = await api.qcm.list(sessionId);
      setQcms(data.qcms.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ));
    } catch (err) {
      console.error("Failed to load QCMs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) { setError("Le sujet est obligatoire."); return; }
    setError("");
    setIsGenerating(true);
    try {
      const qcm = await api.qcm.generate(sessionId, {
        topic: topic.trim(),
        num_questions: numQuestions,
        difficulty,
        title: title.trim() || undefined,
      });
      setQcms(prev => [qcm, ...prev]);
      setShowForm(false);
      setTopic(""); setTitle(""); setNumQuestions(5); setDifficulty("medium");
      router.push(`/sessions/${sessionId}/qcm/${qcm.id}`);
    } catch (err: any) {
      setError(err.message || "Erreur lors de la génération.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Chargement des QCM…</p>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <Link href={`/sessions/${sessionId}`} style={styles.backLink}>
            ← Retour à la session
          </Link>
          <h1 style={styles.title}>
            <span style={styles.titleIcon}>📋</span> QCM
          </h1>
          <p style={styles.subtitle}>
            Générez des questionnaires à choix multiples basés sur vos documents
          </p>
        </div>
        <div style={styles.headerActions}>
          <button
            onClick={() => setShowWorkflow(!showWorkflow)}
            style={{ ...styles.btnSecondary, marginRight: 8 }}
          >
            🔗 Workflow
          </button>
          <button onClick={() => setShowForm(!showForm)} style={styles.btnPrimary}>
            {showForm ? "✕ Annuler" : "+ Nouveau QCM"}
          </button>
        </div>
      </div>

      {/* Workflow badge */}
      {showWorkflow && (
        <div style={styles.workflowBanner}>
          <span style={styles.workflowBannerText}>
            🔍 Visualiser le pipeline LangGraph complet →
          </span>
          <Link
            href={`/sessions/${sessionId}/qcm/workflow`}
            style={styles.workflowLink}
          >
            Ouvrir la visualisation
          </Link>
        </div>
      )}

      {/* Generation Form */}
      {showForm && (
        <div style={styles.formCard}>
          <h2 style={styles.formTitle}>Nouveau QCM</h2>
          <form onSubmit={handleGenerate}>
            <div style={styles.formGrid}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Sujet *</label>
                <input
                  style={styles.input}
                  placeholder="Ex : Les dérivées, La photosynthèse…"
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                  required
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Titre (optionnel)</label>
                <input
                  style={styles.input}
                  placeholder="Titre du QCM"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Nombre de questions</label>
                <div style={styles.sliderContainer}>
                  <input
                    type="range" min={1} max={20} value={numQuestions}
                    onChange={e => setNumQuestions(Number(e.target.value))}
                    style={styles.slider}
                  />
                  <span style={styles.sliderValue}>{numQuestions}</span>
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Difficulté</label>
                <div style={styles.difficultyButtons}>
                  {(["easy", "medium", "hard"] as QCMDifficulty[]).map(d => (
                    <button
                      key={d} type="button"
                      onClick={() => setDifficulty(d)}
                      style={{
                        ...styles.difficultyBtn,
                        ...(difficulty === d ? {
                          background: DIFFICULTY_COLORS[d],
                          color: "#fff",
                          borderColor: DIFFICULTY_COLORS[d],
                        } : {}),
                      }}
                    >
                      {DIFFICULTY_LABELS[d]}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            {error && <p style={styles.errorText}>{error}</p>}
            <button
              type="submit"
              style={{ ...styles.btnPrimary, width: "100%", marginTop: 16 }}
              disabled={isGenerating}
            >
              {isGenerating ? "⏳ Génération en cours…" : "🚀 Générer le QCM"}
            </button>
          </form>
        </div>
      )}

      {/* QCM List */}
      {qcms.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📋</div>
          <p style={styles.emptyTitle}>Aucun QCM pour l'instant</p>
          <p style={styles.emptySubtitle}>
            Générez votre premier QCM à partir de vos documents
          </p>
          <button onClick={() => setShowForm(true)} style={styles.btnPrimary}>
            + Créer un QCM
          </button>
        </div>
      ) : (
        <div style={styles.qcmGrid}>
          {qcms.map(qcm => (
            <Link
              key={qcm.id}
              href={`/sessions/${sessionId}/qcm/${qcm.id}`}
              style={styles.qcmCard}
            >
              <div style={styles.qcmCardHeader}>
                <div style={styles.qcmMeta}>
                  <span style={{
                    ...styles.difficultyTag,
                    background: DIFFICULTY_COLORS[qcm.difficulty] + "22",
                    color: DIFFICULTY_COLORS[qcm.difficulty],
                    borderColor: DIFFICULTY_COLORS[qcm.difficulty] + "44",
                  }}>
                    {DIFFICULTY_LABELS[qcm.difficulty]}
                  </span>
                  <span style={{
                    ...styles.statusTag,
                    background: qcm.status === "evaluated" ? "#22c55e22" : "#64748b22",
                    color: qcm.status === "evaluated" ? "#22c55e" : "#64748b",
                  }}>
                    {STATUS_LABELS[qcm.status]}
                  </span>
                </div>
                {qcm.grade_report && (
                  <div style={{
                    ...styles.gradeCircle,
                    background: GRADE_COLORS[qcm.grade_report.grade_letter] + "22",
                    color: GRADE_COLORS[qcm.grade_report.grade_letter],
                    borderColor: GRADE_COLORS[qcm.grade_report.grade_letter],
                  }}>
                    {qcm.grade_report.grade_letter}
                  </div>
                )}
              </div>
              <h3 style={styles.qcmTitle}>{qcm.title}</h3>
              <p style={styles.qcmTopic}>📌 {qcm.topic}</p>
              <div style={styles.qcmFooter}>
                <span style={styles.qcmStats}>
                  {qcm.num_questions} questions
                  {qcm.grade_report ? ` · ${qcm.grade_report.total_score.toFixed(0)}%` : ""}
                </span>
                <span style={styles.qcmDate}>
                  {new Date(qcm.created_at).toLocaleDateString("fr-FR")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "#0f172a",
    color: "#e2e8f0",
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
    padding: "32px 24px",
    maxWidth: 1100,
    margin: "0 auto",
  },
  loadingContainer: {
    minHeight: "100vh",
    background: "#0f172a",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
  },
  spinner: {
    width: 40,
    height: 40,
    border: "3px solid #1e293b",
    borderTop: "3px solid #6366f1",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  loadingText: { color: "#64748b", fontSize: 14 },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 32,
    flexWrap: "wrap",
    gap: 16,
  },
  headerLeft: { display: "flex", flexDirection: "column", gap: 4 },
  headerActions: { display: "flex", alignItems: "center" },
  backLink: {
    color: "#6366f1",
    textDecoration: "none",
    fontSize: 14,
    marginBottom: 8,
  },
  title: { fontSize: 28, fontWeight: 700, color: "#f1f5f9", margin: 0 },
  titleIcon: { marginRight: 8 },
  subtitle: { color: "#64748b", fontSize: 14, margin: 0 },
  btnPrimary: {
    background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    transition: "opacity .2s",
  },
  btnSecondary: {
    background: "#1e293b",
    color: "#94a3b8",
    border: "1px solid #334155",
    borderRadius: 10,
    padding: "10px 16px",
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
  },
  workflowBanner: {
    background: "#1e293b",
    border: "1px solid #6366f133",
    borderRadius: 10,
    padding: "12px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 24,
  },
  workflowBannerText: { color: "#94a3b8", fontSize: 14 },
  workflowLink: {
    color: "#6366f1",
    textDecoration: "none",
    fontSize: 14,
    fontWeight: 600,
  },
  formCard: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 16,
    padding: 28,
    marginBottom: 32,
  },
  formTitle: { fontSize: 18, fontWeight: 600, color: "#f1f5f9", marginBottom: 20 },
  formGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 },
  formGroup: { display: "flex", flexDirection: "column", gap: 8 },
  label: { fontSize: 13, fontWeight: 500, color: "#94a3b8" },
  input: {
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 8,
    padding: "10px 14px",
    color: "#e2e8f0",
    fontSize: 14,
    outline: "none",
  },
  sliderContainer: { display: "flex", alignItems: "center", gap: 12 },
  slider: { flex: 1, accentColor: "#6366f1" },
  sliderValue: {
    background: "#6366f1",
    color: "#fff",
    borderRadius: 6,
    padding: "2px 10px",
    fontWeight: 700,
    fontSize: 16,
    minWidth: 36,
    textAlign: "center",
  },
  difficultyButtons: { display: "flex", gap: 8 },
  difficultyBtn: {
    flex: 1,
    padding: "8px 0",
    border: "1px solid #334155",
    borderRadius: 8,
    background: "transparent",
    color: "#94a3b8",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    transition: "all .15s",
  },
  errorText: { color: "#ef4444", fontSize: 13, marginTop: 8 },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: "80px 0",
    color: "#64748b",
  },
  emptyIcon: { fontSize: 56 },
  emptyTitle: { fontSize: 18, fontWeight: 600, color: "#94a3b8" },
  emptySubtitle: { fontSize: 14, marginBottom: 8 },
  qcmGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: 20,
  },
  qcmCard: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 14,
    padding: 20,
    textDecoration: "none",
    color: "#e2e8f0",
    transition: "border-color .2s, transform .15s",
    display: "block",
    cursor: "pointer",
  },
  qcmCardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  qcmMeta: { display: "flex", gap: 8, flexWrap: "wrap" },
  difficultyTag: {
    fontSize: 11,
    fontWeight: 600,
    padding: "3px 8px",
    borderRadius: 6,
    border: "1px solid",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  statusTag: {
    fontSize: 11,
    fontWeight: 500,
    padding: "3px 8px",
    borderRadius: 6,
  },
  gradeCircle: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    border: "2px solid",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 800,
    fontSize: 16,
  },
  qcmTitle: { fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 6 },
  qcmTopic: { fontSize: 13, color: "#94a3b8", marginBottom: 14 },
  qcmFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderTop: "1px solid #334155",
    paddingTop: 12,
  },
  qcmStats: { fontSize: 13, color: "#6366f1", fontWeight: 500 },
  qcmDate: { fontSize: 12, color: "#475569" },
};
