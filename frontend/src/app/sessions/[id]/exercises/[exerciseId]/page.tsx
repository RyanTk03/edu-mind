"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { exercises as exercisesApi } from "@/lib/api";
import { Exercise, Question, QuestionType } from "@/types";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const TYPE_LABELS: Record<QuestionType, string> = {
  qcm: "QCM",
  open: "Ouverte",
  code: "Code",
};

function ScoreRing({ score }: { score: number }) {
  const radius = 36;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;
  const color =
    score >= 80 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="-rotate-90 w-24 h-24 absolute">
        <circle cx="48" cy="48" r={radius} strokeWidth="8" stroke="#f4f4f5" fill="none" />
        <circle
          cx="48"
          cy="48"
          r={radius}
          strokeWidth="8"
          stroke={color}
          fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <span className="relative text-xl font-bold text-zinc-900">{score}%</span>
    </div>
  );
}

// ─── Question Card ────────────────────────────────────────────────────────────

function QuestionCard({
  question,
  index,
  showResults,
}: {
  question: Question;
  index: number;
  showResults: boolean;
}) {
  const isCorrect = question.is_correct;
  const answered = question.user_answer !== null;

  let borderColor = "border-zinc-200";
  if (showResults && answered) {
    borderColor = isCorrect ? "border-green-300" : "border-red-300";
  }
console.log(question);
  return (
    <div className={`bg-white border-2 ${borderColor} rounded-2xl p-5 transition-colors`}>
      <div className="flex items-start gap-3">
        {/* Index badge */}
        <span
          className={`shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold ${
            showResults && answered
              ? isCorrect
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-600"
              : "bg-zinc-100 text-zinc-500"
          }`}
        >
          {index + 1}
        </span>

        <div className="flex-1 min-w-0">
          {/* Type tag */}
          <span className="text-xs font-medium text-zinc-400 mb-1.5 block">
            {TYPE_LABELS[question.type]}
          </span>

          {/* Question text */}
          <p className="text-sm font-medium text-zinc-900 leading-relaxed">
            {question.question_text}
          </p>

          {/* Options (QCM) */}
          {question.type === "qcm" && question.options.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {question.options.map((opt) => {
                const isSelected = question.user_answer === opt.label;
                const isCorrectOpt =
                  showResults && question.correct_answer === opt.label;
                const isWrong = showResults && isSelected && !isCorrect;

                return (
                  <li
                    key={opt.label}
                    className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-sm border transition-colors ${
                      isCorrectOpt
                        ? "bg-green-50 border-green-200 text-green-800"
                        : isWrong
                        ? "bg-red-50 border-red-200 text-red-700 line-through"
                        : isSelected
                        ? "bg-zinc-100 border-zinc-300 text-zinc-800"
                        : "bg-zinc-50 border-zinc-100 text-zinc-600"
                    }`}
                  >
                    <span
                      className={`w-5 h-5 shrink-0 flex items-center justify-center rounded-full text-xs font-bold border ${
                        isCorrectOpt
                          ? "bg-green-200 border-green-300 text-green-800"
                          : isWrong
                          ? "bg-red-200 border-red-300 text-red-700"
                          : "bg-white border-zinc-200 text-zinc-500"
                      }`}
                    >
                      {opt.label}
                    </span>
                    {opt.text}
                  </li>
                );
              })}
            </ul>
          )}

          {/* User answer (open / code) */}
          {question.type !== "qcm" && question.user_answer && (
            <div className="mt-3">
              <p className="text-xs text-zinc-400 mb-1.5 font-medium">Votre réponse</p>
              <pre
                className={`text-sm rounded-xl px-4 py-3 font-mono whitespace-pre-wrap border ${
                  showResults
                    ? isCorrect
                      ? "bg-green-50 border-green-200 text-green-900"
                      : "bg-red-50 border-red-200 text-red-800"
                    : "bg-zinc-50 border-zinc-200 text-zinc-800"
                }`}
              >
                {question.user_answer}
              </pre>
            </div>
          )}

          {/* Correct answer + gap analysis */}
          {showResults && !isCorrect && question.correct_answer && (
            <div className="mt-3 space-y-2">
              <div>
                <p className="text-xs font-medium text-zinc-400 mb-1">Bonne réponse</p>
                <p className="text-sm text-green-800 bg-green-50 border border-green-200 rounded-xl px-3.5 py-2.5">
                  {question.correct_answer}
                </p>
              </div>
              {question.gap_analysis && (
                <div>
                  <p className="text-xs font-medium text-zinc-400 mb-1">Analyse</p>
                  <p className="text-sm text-zinc-600 bg-amber-50 border border-amber-100 rounded-xl px-3.5 py-2.5 leading-relaxed">
                    {question.gap_analysis}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ExerciseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const exerciseId = params.exerciseId as string;

  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isCompleted = exercise?.status === "completed";

  useEffect(() => {
    setLoading(true);
    const fetch = isCompleted
      ? exercisesApi.getResults(sessionId, exerciseId)
      : exercisesApi.get(sessionId, exerciseId);

    fetch
      .then(setExercise)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Erreur de chargement.")
      )
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, exerciseId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-zinc-200 border-t-zinc-800 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !exercise) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
        <div className="text-center px-4">
          <p className="text-red-500 mb-4">{error ?? "Exercice introuvable."}</p>
          <button
            onClick={() => router.back()}
            className="text-sm text-zinc-600 underline"
          >
            Retour
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = exercise.questions.filter(
    (q) => q.user_answer !== null
  ).length;
  const correctCount = exercise.questions.filter((q) => q.is_correct).length;

  return (
    <div className="min-h-screen bg-zinc-50">
      <div className="max-w-3xl mx-auto px-4 py-10">
        {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-700 transition-colors mb-6 group"
        >
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          Exercices
        </button>

        {/* Header */}
        <div className="bg-white border border-zinc-200 rounded-2xl p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-zinc-900 leading-tight">
                {exercise.title}
              </h1>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className="text-xs font-medium text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-full">
                  {exercise.mode === "evaluation"
                    ? "Évaluation"
                    : exercise.mode === "reinforcement"
                    ? "Renforcement"
                    : "Libre"}
                </span>
                <span className="text-xs text-zinc-400">
                  {exercise.questions.length} question
                  {exercise.questions.length !== 1 ? "s" : ""}
                </span>
                {isCompleted && exercise.completed_at && (
                  <span className="text-xs text-zinc-400">
                    Complété le{" "}
                    {new Date(exercise.completed_at).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                )}
              </div>
            </div>

            {/* Score ring — only when completed */}
            {isCompleted && exercise.total_score !== null && (
              <ScoreRing score={exercise.total_score} />
            )}
          </div>

          {/* Stats bar — only when completed */}
          {isCompleted && (
            <div className="mt-5 pt-5 border-t border-zinc-100 grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-zinc-900">{correctCount}</p>
                <p className="text-xs text-zinc-400 mt-0.5">Correctes</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-zinc-900">
                  {exercise.questions.length - correctCount}
                </p>
                <p className="text-xs text-zinc-400 mt-0.5">Incorrectes</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-zinc-900">{answeredCount}</p>
                <p className="text-xs text-zinc-400 mt-0.5">Répondues</p>
              </div>
            </div>
          )}
        </div>

        {/* Questions */}
        <div className="space-y-3">
          {exercise.questions
            .slice()
            .sort((a, b) => a.order - b.order)
            .map((q, i) => (
              <QuestionCard
                key={q.order}
                question={q}
                index={i}
                showResults={isCompleted}
              />
            ))}
        </div>

        {/* CTA — start exercise if pending */}
        {exercise.status !== "completed" && (
          <div className="mt-8 text-center">
            <button
              onClick={() =>
                router.push(
                  `/sessions/${sessionId}/exercises/${exerciseId}/start`
                )
              }
              className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 text-white font-semibold text-sm rounded-xl hover:bg-zinc-700 transition-colors shadow-sm"
            >
              Commencer l&apos;exercice →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
