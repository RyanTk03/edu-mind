"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import type { QCM, QCMQuestion } from "@/types";

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Facile",
  medium: "Intermédiaire",
  hard: "Difficile",
};

const GRADE_COLORS: Record<string, string> = {
  A: "#22c55e", B: "#84cc16", C: "#f59e0b", D: "#f97316", F: "#ef4444",
};

export default function QCMDetailPage() {
  const params  = useParams();
  const router  = useRouter();
  const sessionId = params.id as string;
  const qcmId   = params.qcmId as string;

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [qcm, setQcm]         = useState<QCM | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [phase, setPhase] = useState<"answering" | "results">("answering");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && sessionId && qcmId) loadQCM();
  }, [isAuthenticated, sessionId, qcmId]);

  const loadQCM = async () => {
    try {
      let data: QCM;
      // Try results first (if already evaluated)
      try {
        data = await api.qcm.getResults(sessionId, qcmId);
        setPhase("results");
      } catch {
        data = await api.qcm.get(sessionId, qcmId);
        if (data.status === "evaluated") setPhase("results");
      }
      setQcm(data);
    } catch (err) {
      console.error("Failed to load QCM:", err);
      router.push(`/sessions/${sessionId}/qcm`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswer = (order: number, label: string) => {
    setAnswers(prev => ({ ...prev, [order]: label }));
  };

  const handleSubmit = async () => {
    if (!qcm) return;
    const unanswered = qcm.questions.filter(q => !answers[q.order]);
    if (unanswered.length > 0) {
      setError(`Veuillez répondre à toutes les questions (${unanswered.length} restante${unanswered.length > 1 ? "s" : ""}).`);
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      const result = await api.qcm.submit(sessionId, qcmId, {
        answers: Object.entries(answers).map(([order, answer]) => ({
          question_order: Number(order),
          answer,
        })),
      });
      setQcm(result);
      setPhase("results");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      setError(err.message || "Erreur lors de la soumission.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Chargement du QCM…</p>
      </div>
    );
  }

  if (!qcm) return null;

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <Link href={`/sessions/${sessionId}/qcm`} style={styles.backLink}>
          ← Retour aux QCM
        </Link>
        <div style={styles.headerRow}>
          <div>
            <h1 style={styles.title}>{qcm.title}</h1>
            <div style={styles.metaRow}>
              <span style={styles.metaBadge}>📌 {qcm.topic}</span>
              <span style={styles.metaBadge}>
                🎯 {DIFFICULTY_LABELS[qcm.difficulty]}
              </span>
              <span style={styles.metaBadge}>
                ❓ {qcm.num_questions} questions
              </span>
            </div>
          </div>
          {phase === "results" && qcm.grade_report && (
            <div style={{
              ...styles.gradeCircleLarge,
              color: GRADE_COLORS[qcm.grade_report.grade_letter],
              borderColor: GRADE_COLORS[qcm.grade_report.grade_letter],
              background: GRADE_COLORS[qcm.grade_report.grade_letter] + "18",
            }}>
              <span style={styles.gradeLetter}>{qcm.grade_report.grade_letter}</span>
              <span style={styles.gradeScore}>
                {qcm.grade_report.total_score.toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Grade Report (results phase) */}
      {phase === "results" && qcm.grade_report && (
        <GradeReportCard report={qcm.grade_report} />
      )}

      {/* Progress bar (answering phase) */}
      {phase === "answering" && (
        <div style={styles.progressContainer}>
          <div style={styles.progressInfo}>
            <span style={styles.progressText}>
              {Object.keys(answers).length} / {qcm.num_questions} réponses
            </span>
          </div>
          <div style={styles.progressBar}>
            <div style={{
              ...styles.progressFill,
              width: `${(Object.keys(answers).length / qcm.num_questions) * 100}%`,
            }} />
          </div>
        </div>
      )}

      {/* Questions */}
      <div style={styles.questionsList}>
        {qcm.questions.map((q, idx) => (
          <QuestionCard
            key={q.order}
            question={q}
            index={idx}
            selectedAnswer={answers[q.order]}
            onSelect={handleAnswer}
            phase={phase}
          />
        ))}
      </div>

      {/* Answering phase: submit button */}
      {phase === "answering" && (
        <div style={styles.submitSection}>
          {error && <p style={styles.errorText}>{error}</p>}
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            style={{
              ...styles.btnSubmit,
              opacity: isSubmitting ? 0.6 : 1,
            }}
          >
            {isSubmitting
              ? "⏳ Correction en cours…"
              : `✅ Soumettre (${Object.keys(answers).length}/${qcm.num_questions})`}
          </button>
        </div>
      )}

      {/* Results phase: action buttons */}
      {phase === "results" && (
        <div style={styles.resultActions}>
          <Link href={`/sessions/${sessionId}/qcm`} style={styles.btnSecondary}>
            ← Retour aux QCM
          </Link>
          <Link href={`/sessions/${sessionId}/qcm/workflow`} style={styles.btnWorkflow}>
            🔗 Voir le pipeline
          </Link>
        </div>
      )}
    </div>
  );
}

// ── Question Card ─────────────────────────────────────────────────────────────

function QuestionCard({
  question,
  index,
  selectedAnswer,
  onSelect,
  phase,
}: {
  question: QCMQuestion;
  index: number;
  selectedAnswer?: string;
  onSelect: (order: number, label: string) => void;
  phase: "answering" | "results";
}) {
  const isResults = phase === "results";

  return (
    <div style={{
      ...styles.questionCard,
      borderColor: isResults
        ? question.is_correct === true ? "#22c55e44"
          : question.is_correct === false ? "#ef444444"
          : "#334155"
        : "#334155",
    }}>
      <div style={styles.questionHeader}>
        <span style={styles.questionNumber}>Q{question.order}</span>
        {isResults && question.is_correct !== null && (
          <span style={{
            fontSize: 13,
            fontWeight: 600,
            color: question.is_correct ? "#22c55e" : "#ef4444",
          }}>
            {question.is_correct ? "✓ Correct" : "✗ Incorrect"}
          </span>
        )}
      </div>
      <p style={styles.questionText}>{question.question_text}</p>

      <div style={styles.optionsList}>
        {question.options.map(option => {
          const isSelected = selectedAnswer === option.label;
          const isCorrectAnswer = isResults && question.correct_answer === option.label;
          const isWrongSelected = isResults && isSelected && !question.is_correct;

          let optionStyle = { ...styles.optionBtn };
          if (isCorrectAnswer) {
            optionStyle = { ...optionStyle, ...styles.optionCorrect };
          } else if (isWrongSelected) {
            optionStyle = { ...optionStyle, ...styles.optionWrong };
          } else if (isSelected && !isResults) {
            optionStyle = { ...optionStyle, ...styles.optionSelected };
          }

          return (
            <button
              key={option.label}
              onClick={() => !isResults && onSelect(question.order, option.label)}
              disabled={isResults}
              style={optionStyle}
            >
              <span style={styles.optionLabel}>{option.label}</span>
              <span style={styles.optionText}>{option.text}</span>
              {isCorrectAnswer && isResults && (
                <span style={styles.optionCorrectIcon}>✓</span>
              )}
              {isWrongSelected && (
                <span style={styles.optionWrongIcon}>✗</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Results extras */}
      {isResults && question.explanation && (
        <div style={styles.explanationBox}>
          <p style={styles.explanationLabel}>📖 Explication</p>
          <p style={styles.explanationText}>{question.explanation}</p>
        </div>
      )}
      {isResults && !question.is_correct && question.gap_analysis && (
        <div style={styles.gapBox}>
          <p style={styles.gapLabel}>🔍 Analyse de l'erreur</p>
          <p style={styles.gapText}>{question.gap_analysis}</p>
        </div>
      )}
      {isResults && question.feedback && (
        <div style={styles.feedbackBox}>
          <p style={styles.feedbackText}>💡 {question.feedback}</p>
        </div>
      )}
    </div>
  );
}

// ── Grade Report Card ─────────────────────────────────────────────────────────

function GradeReportCard({ report }: { report: NonNullable<QCM["grade_report"]> }) {
  const color = GRADE_COLORS[report.grade_letter];
  return (
    <div style={{ ...styles.gradeReport, borderColor: color + "44" }}>
      <div style={styles.gradeReportHeader}>
        <div>
          <p style={{ ...styles.gradeLabel_, color }}>
            {report.grade_label}
          </p>
          <p style={styles.gradeScoreText}>
            {report.correct_count}/{report.total_questions} correctes · {report.total_score.toFixed(1)}%
          </p>
        </div>
      </div>
      {report.summary && (
        <p style={styles.gradeSummary}>{report.summary}</p>
      )}
      <div style={styles.gradeColumns}>
        {report.strong_points.length > 0 && (
          <div>
            <p style={{ ...styles.gradeColTitle, color: "#22c55e" }}>✅ Points forts</p>
            <ul style={styles.gradeList}>
              {report.strong_points.map((p, i) => (
                <li key={i} style={{ ...styles.gradeListItem, color: "#86efac" }}>{p}</li>
              ))}
            </ul>
          </div>
        )}
        {report.weak_points.length > 0 && (
          <div>
            <p style={{ ...styles.gradeColTitle, color: "#f59e0b" }}>⚠️ À retravailler</p>
            <ul style={styles.gradeList}>
              {report.weak_points.map((p, i) => (
                <li key={i} style={{ ...styles.gradeListItem, color: "#fcd34d" }}>{p}</li>
              ))}
            </ul>
          </div>
        )}
        {report.recommendations.length > 0 && (
          <div>
            <p style={{ ...styles.gradeColTitle, color: "#6366f1" }}>💡 Recommandations</p>
            <ul style={styles.gradeList}>
              {report.recommendations.map((r, i) => (
                <li key={i} style={{ ...styles.gradeListItem, color: "#a5b4fc" }}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
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
    maxWidth: 860,
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
    width: 40, height: 40,
    border: "3px solid #1e293b",
    borderTop: "3px solid #6366f1",
    borderRadius: "50%",
  },
  loadingText: { color: "#64748b", fontSize: 14 },
  header: { marginBottom: 28 },
  backLink: {
    color: "#6366f1", textDecoration: "none", fontSize: 14,
    display: "block", marginBottom: 14,
  },
  headerRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  title: { fontSize: 24, fontWeight: 700, color: "#f1f5f9", marginBottom: 10 },
  metaRow: { display: "flex", gap: 10, flexWrap: "wrap" },
  metaBadge: {
    fontSize: 12, color: "#94a3b8",
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 6, padding: "3px 10px",
  },
  gradeCircleLarge: {
    display: "flex", flexDirection: "column", alignItems: "center",
    justifyContent: "center", width: 76, height: 76,
    borderRadius: "50%", border: "3px solid",
    flexShrink: 0,
  },
  gradeLetter: { fontSize: 28, fontWeight: 800, lineHeight: 1 },
  gradeScore: { fontSize: 11, fontWeight: 600, opacity: 0.8 },
  progressContainer: { marginBottom: 24 },
  progressInfo: { display: "flex", justifyContent: "flex-end", marginBottom: 6 },
  progressText: { fontSize: 13, color: "#94a3b8" },
  progressBar: {
    height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: "linear-gradient(90deg,#6366f1,#8b5cf6)",
    borderRadius: 3,
    transition: "width .3s ease",
  },
  questionsList: { display: "flex", flexDirection: "column", gap: 20, marginBottom: 32 },
  questionCard: {
    background: "#1e293b",
    border: "1px solid",
    borderRadius: 14,
    padding: 24,
    transition: "border-color .2s",
  },
  questionHeader: {
    display: "flex", justifyContent: "space-between",
    alignItems: "center", marginBottom: 12,
  },
  questionNumber: {
    fontSize: 12, fontWeight: 700, color: "#6366f1",
    background: "#6366f122", border: "1px solid #6366f133",
    borderRadius: 6, padding: "2px 8px", letterSpacing: "0.05em",
  },
  questionText: { fontSize: 16, color: "#f1f5f9", lineHeight: 1.6, marginBottom: 18 },
  optionsList: { display: "flex", flexDirection: "column", gap: 10 },
  optionBtn: {
    display: "flex", alignItems: "center", gap: 12,
    background: "#0f172a", border: "1px solid #334155",
    borderRadius: 10, padding: "12px 16px",
    cursor: "pointer", textAlign: "left", color: "#cbd5e1",
    fontSize: 14, transition: "all .15s", width: "100%",
  },
  optionSelected: {
    background: "#6366f118", borderColor: "#6366f1",
    color: "#a5b4fc",
  },
  optionCorrect: {
    background: "#22c55e18", borderColor: "#22c55e",
    color: "#86efac",
  },
  optionWrong: {
    background: "#ef444418", borderColor: "#ef4444",
    color: "#fca5a5",
  },
  optionLabel: {
    background: "#334155", color: "#94a3b8",
    fontWeight: 700, fontSize: 13,
    width: 28, height: 28, borderRadius: 6,
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  optionText: { flex: 1 },
  optionCorrectIcon: { color: "#22c55e", fontWeight: 700, marginLeft: "auto" },
  optionWrongIcon: { color: "#ef4444", fontWeight: 700, marginLeft: "auto" },
  explanationBox: {
    marginTop: 16, background: "#0f172a",
    border: "1px solid #22c55e33", borderRadius: 8, padding: 14,
  },
  explanationLabel: { fontSize: 12, fontWeight: 600, color: "#22c55e", marginBottom: 6 },
  explanationText: { fontSize: 13, color: "#86efac", lineHeight: 1.6 },
  gapBox: {
    marginTop: 10, background: "#0f172a",
    border: "1px solid #f59e0b33", borderRadius: 8, padding: 14,
  },
  gapLabel: { fontSize: 12, fontWeight: 600, color: "#f59e0b", marginBottom: 6 },
  gapText: { fontSize: 13, color: "#fcd34d", lineHeight: 1.6 },
  feedbackBox: {
    marginTop: 10, background: "#6366f110",
    border: "1px solid #6366f133", borderRadius: 8, padding: 14,
  },
  feedbackText: { fontSize: 13, color: "#a5b4fc", lineHeight: 1.6 },
  submitSection: {
    display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
  },
  errorText: { color: "#ef4444", fontSize: 13 },
  btnSubmit: {
    background: "linear-gradient(135deg,#22c55e,#16a34a)",
    color: "#fff", border: "none",
    borderRadius: 12, padding: "14px 40px",
    fontSize: 16, fontWeight: 700, cursor: "pointer",
    transition: "opacity .2s",
  },
  resultActions: {
    display: "flex", justifyContent: "center", gap: 16, marginTop: 32,
  },
  btnSecondary: {
    background: "#1e293b", color: "#94a3b8",
    border: "1px solid #334155",
    borderRadius: 10, padding: "10px 20px",
    fontSize: 14, fontWeight: 500,
    textDecoration: "none", display: "inline-block",
  },
  btnWorkflow: {
    background: "#6366f120", color: "#818cf8",
    border: "1px solid #6366f133",
    borderRadius: 10, padding: "10px 20px",
    fontSize: 14, fontWeight: 500,
    textDecoration: "none", display: "inline-block",
  },
  // Grade report
  gradeReport: {
    background: "#1e293b", border: "1px solid",
    borderRadius: 16, padding: 24, marginBottom: 28,
  },
  gradeReportHeader: {
    display: "flex", justifyContent: "space-between",
    alignItems: "center", marginBottom: 14,
  },
  gradeLabel_: { fontSize: 22, fontWeight: 800, marginBottom: 4 },
  gradeScoreText: { fontSize: 14, color: "#94a3b8" },
  gradeSummary: {
    fontSize: 14, color: "#cbd5e1", lineHeight: 1.7,
    borderLeft: "3px solid #6366f1",
    paddingLeft: 14, marginBottom: 20, fontStyle: "italic",
  },
  gradeColumns: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 16,
  },
  gradeColTitle: { fontSize: 13, fontWeight: 700, marginBottom: 8 },
  gradeList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 },
  gradeListItem: { fontSize: 13, paddingLeft: 12, position: "relative" },
};
