"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { exercises as exercisesApi } from "@/lib/api";
import { Exercise, Question, AnswerSubmission } from "@/types";

// ─── Progress Bar ─────────────────────────────────────────────────────────────

function ProgressBar({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  const pct = Math.round((current / total) * 100);
  return (
    <div className="w-full h-1.5 bg-zinc-100 rounded-full overflow-hidden">
      <div
        className="h-full bg-zinc-900 rounded-full transition-all duration-500 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ─── QCM Input ────────────────────────────────────────────────────────────────

function QcmInput({
  question,
  value,
  onChange,
}: {
  question: Question;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <ul className="space-y-2.5">
      {question.options.map((opt) => {
        const selected = value === opt.label;
        return (
          <li key={opt.label}>
            <button
              onClick={() => onChange(opt.label)}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-xl border-2 text-sm text-left transition-all duration-150 ${
                selected
                  ? "border-zinc-900 bg-zinc-900 text-white shadow-sm"
                  : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50"
              }`}
            >
              <span
                className={`w-6 h-6 shrink-0 flex items-center justify-center rounded-full text-xs font-bold border transition-colors ${
                  selected
                    ? "border-white/30 text-white"
                    : "border-zinc-300 text-zinc-500"
                }`}
              >
                {opt.label}
              </span>
              {opt.text}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// ─── Open Input ───────────────────────────────────────────────────────────────

function OpenInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={5}
      placeholder="Rédigez votre réponse…"
      className="w-full px-4 py-3.5 text-sm text-zinc-900 bg-zinc-50 border-2 border-zinc-200 rounded-xl placeholder:text-zinc-400 focus:outline-none focus:border-zinc-400 focus:bg-white transition resize-none leading-relaxed"
    />
  );
}

// ─── Code Input ───────────────────────────────────────────────────────────────

function CodeInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative">
      <div className="absolute top-0 left-0 right-0 h-9 bg-zinc-800 rounded-t-xl flex items-center px-4 gap-1.5">
        {["bg-red-400", "bg-amber-400", "bg-green-400"].map((c, i) => (
          <span key={i} className={`w-2.5 h-2.5 rounded-full ${c}`} />
        ))}
        <span className="ml-2 text-xs text-zinc-400 font-mono">answer.txt</span>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={8}
        placeholder="// Écrivez votre code ici…"
        spellCheck={false}
        className="w-full pt-12 pb-4 px-4 font-mono text-sm text-green-300 bg-zinc-900 border-2 border-zinc-700 rounded-xl placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500 transition resize-none leading-relaxed"
      />
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ExerciseStartPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const exerciseId = params.exerciseId as string;

  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // answers keyed by question order
  const [answers, setAnswers] = useState<Record<number, string>>({});

  // current step index (0-based)
  const [step, setStep] = useState(0);

  // submit state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // confirmation before leaving
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    exercisesApi
      .get(sessionId, exerciseId)
      .then((ex) => {
        if (ex.status === "completed") {
          router.replace(`/sessions/${sessionId}/exercises/${exerciseId}`);
          return;
        }
        const sorted = [...ex.questions].sort((a, b) => a.order - b.order);
        setExercise({ ...ex, questions: sorted });
        // pre-fill any existing answers
        const pre: Record<number, string> = {};
        sorted.forEach((q) => {
          if (q.user_answer !== null) pre[q.order] = q.user_answer;
        });
        setAnswers(pre);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Erreur de chargement.")
      )
      .finally(() => setLoading(false));
  }, [sessionId, exerciseId, router]);

  const questions = useMemo(() => exercise?.questions ?? [], [exercise?.questions]);
  const total = questions.length;
  const currentQ: Question | undefined = questions[step];
  const currentAnswer = currentAnswer_value();

  function currentAnswer_value() {
    if (!currentQ) return "";
    return answers[currentQ.order] ?? "";
  }

  function setCurrentAnswer(val: string) {
    if (!currentQ) return;
    setAnswers((prev) => ({ ...prev, [currentQ.order]: val }));
  }

  const isLast = step === total - 1;
  const canProceed = currentAnswer.trim().length > 0;

  function goNext() {
    if (step < total - 1) setStep((s) => s + 1);
  }

  function goPrev() {
    if (step > 0) setStep((s) => s - 1);
  }

  const handleSubmit = useCallback(async () => {
    if (!exercise) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload: AnswerSubmission[] = questions.map((q) => ({
        question_order: q.order,
        answer: answers[q.order] ?? "",
      }));
      await exercisesApi.submit(sessionId, exerciseId, { answers: payload });
      router.push(`/sessions/${sessionId}/exercises/${exerciseId}`);
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Erreur lors de la soumission.");
      setSubmitting(false);
    }
  }, [exercise, questions, answers, sessionId, exerciseId, router]);

  // ─── Loading / Error ────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-zinc-200 border-t-zinc-800 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !exercise || !currentQ) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
        <div className="text-center px-4">
          <p className="text-red-500 mb-4">{error ?? "Exercice introuvable."}</p>
          <button onClick={() => router.back()} className="text-sm text-zinc-600 underline">
            Retour
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = questions.filter((q) => (answers[q.order] ?? "").trim()).length;

  // ─── Confirm Submit Modal ───────────────────────────────────────────────────

  const unanswered = total - answeredCount;

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white border-b border-zinc-100 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => setShowConfirm(true)}
            className="text-zinc-400 hover:text-zinc-700 transition-colors text-sm flex items-center gap-1 shrink-0"
          >
            ← Quitter
          </button>
          <div className="flex-1 flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-zinc-500 truncate max-w-[60%]">
                {exercise.title}
              </span>
              <span className="text-xs text-zinc-400 shrink-0">
                {step + 1} / {total}
              </span>
            </div>
            <ProgressBar current={answeredCount} total={total} />
          </div>
        </div>
      </header>

      {/* Question area */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-2xl">
          {/* Question number + type */}
          <div className="flex items-center gap-2 mb-4">
            <span className="w-8 h-8 flex items-center justify-center bg-zinc-900 text-white text-sm font-bold rounded-full">
              {step + 1}
            </span>
            <span className="text-xs font-medium text-zinc-400 bg-zinc-100 px-2.5 py-1 rounded-full">
              {currentQ.type === "qcm"
                ? "QCM"
                : currentQ.type === "open"
                ? "Réponse ouverte"
                : "Code"}
            </span>
          </div>

          {/* Question text */}
          <h2 className="text-lg font-semibold text-zinc-900 leading-relaxed mb-6">
            {currentQ.question_text}
          </h2>

          {/* Input by type */}
          {currentQ.type === "qcm" ? (
            <QcmInput
              question={currentQ}
              value={currentAnswer}
              onChange={setCurrentAnswer}
            />
          ) : currentQ.type === "code" ? (
            <CodeInput value={currentAnswer} onChange={setCurrentAnswer} />
          ) : (
            <OpenInput value={currentAnswer} onChange={setCurrentAnswer} />
          )}

          {submitError && (
            <p className="mt-4 text-sm text-red-500 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {submitError}
            </p>
          )}
        </div>
      </main>

      {/* Bottom nav */}
      <footer className="sticky bottom-0 bg-white border-t border-zinc-100 px-4 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between gap-3">
          <button
            onClick={goPrev}
            disabled={step === 0}
            className="px-4 py-2.5 text-sm font-medium text-zinc-600 hover:text-zinc-900 rounded-xl hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ← Précédent
          </button>

          {/* Dot nav */}
          <div className="flex items-center gap-1.5 flex-wrap justify-center">
            {questions.map((q, i) => {
              const done = (answers[q.order] ?? "").trim().length > 0;
              return (
                <button
                  key={q.order}
                  onClick={() => setStep(i)}
                  className={`w-2 h-2 rounded-full transition-all duration-200 ${
                    i === step
                      ? "w-4 bg-zinc-900"
                      : done
                      ? "bg-zinc-400"
                      : "bg-zinc-200"
                  }`}
                />
              );
            })}
          </div>

          {isLast ? (
            <button
              onClick={() => setShowConfirm(true)}
              disabled={submitting}
              className="px-5 py-2.5 text-sm font-semibold bg-zinc-900 text-white rounded-xl hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {submitting && (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              Soumettre
            </button>
          ) : (
            <button
              onClick={goNext}
              disabled={!canProceed}
              className="px-5 py-2.5 text-sm font-semibold bg-zinc-900 text-white rounded-xl hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Suivant →
            </button>
          )}
        </div>
      </footer>

      {/* Confirm modal */}
      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={(e) => e.target === e.currentTarget && setShowConfirm(false)}
        >
          <div className="bg-white rounded-2xl shadow-2xl border border-zinc-100 w-full max-w-sm mx-4 p-6">
            <h3 className="text-base font-semibold text-zinc-900">
              {submitting
                ? "Soumission en cours…"
                : unanswered > 0
                ? `${unanswered} question${unanswered > 1 ? "s" : ""} sans réponse`
                : "Soumettre l'exercice ?"}
            </h3>
            <p className="text-sm text-zinc-500 mt-2 leading-relaxed">
              {unanswered > 0
                ? `Vous n'avez pas répondu à toutes les questions. Voulez-vous quand même soumettre ? Les questions sans réponse seront comptées comme incorrectes.`
                : "Vous avez répondu à toutes les questions. Cette action est irréversible."}
            </p>

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setShowConfirm(false)}
                disabled={submitting}
                className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 rounded-xl hover:bg-zinc-100 transition-colors disabled:opacity-40"
              >
                Annuler
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-5 py-2 text-sm font-semibold bg-zinc-900 text-white rounded-xl hover:bg-zinc-700 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {submitting && (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                )}
                {submitting ? "Envoi…" : "Confirmer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
