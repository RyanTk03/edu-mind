"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { exercises as exercisesApi } from "@/lib/api";
import {
  Exercise,
  ExerciseMode,
  ExerciseGenerateRequest,
} from "@/types";

// ─── Helpers ────────────────────────────────────────────────────────────────

const MODE_LABELS: Record<ExerciseMode, string> = {
  evaluation: "Évaluation",
  reinforcement: "Renforcement",
  free: "Libre",
};

const MODE_COLORS: Record<ExerciseMode, string> = {
  evaluation: "bg-violet-100 text-violet-700 border-violet-200",
  reinforcement: "bg-sky-100 text-sky-700 border-sky-200",
  free: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const STATUS_COLORS = {
  pending: "bg-zinc-100 text-zinc-500",
  in_progress: "bg-amber-100 text-amber-600",
  completed: "bg-green-100 text-green-700",
};

const STATUS_LABELS = {
  pending: "En attente",
  in_progress: "En cours",
  completed: "Terminé",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

// ─── Create Modal ────────────────────────────────────────────────────────────

interface CreateModalProps {
  onClose: () => void;
  onCreated: (exercise: Exercise) => void;
  sessionId: string;
}

function CreateModal({ onClose, onCreated, sessionId }: CreateModalProps) {
  const [form, setForm] = useState<ExerciseGenerateRequest>({
    mode: "evaluation",
    title: "",
    num_questions: 5,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      const payload: ExerciseGenerateRequest = {
        mode: form.mode,
        ...(form.title?.trim() ? { title: form.title.trim() } : {}),
        num_questions: form.num_questions,
      };
      const exercise = await exercisesApi.generate(sessionId, payload);
      onCreated(exercise);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="relative w-full max-w-md mx-4 bg-white rounded-2xl shadow-2xl border border-zinc-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-zinc-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-900">
              Nouvel exercice
            </h2>
            <p className="text-sm text-zinc-400 mt-0.5">
              Générer un exercice pour cette session
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <div className="px-6 py-5 space-y-5">
          {/* Title */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-zinc-700">
              Titre <span className="text-zinc-400 font-normal">(optionnel)</span>
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Ex: Les bases de la photosynthèse…"
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-zinc-200 bg-zinc-50 text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition"
            />
          </div>

          {/* Mode */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-zinc-700">
              Mode
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(MODE_LABELS) as ExerciseMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setForm((f) => ({ ...f, mode }))}
                  className={`py-2.5 px-3 rounded-xl text-sm font-medium border transition-all ${
                    form.mode === mode
                      ? "bg-zinc-900 text-white border-zinc-900 shadow-sm"
                      : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50"
                  }`}
                >
                  {MODE_LABELS[mode]}
                </button>
              ))}
            </div>
          </div>

          {/* Num questions */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-zinc-700">
              Nombre de questions
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={1}
                max={20}
                value={form.num_questions}
                onChange={(e) =>
                  setForm((f) => ({ ...f, num_questions: Number(e.target.value) }))
                }
                className="flex-1 accent-zinc-900"
              />
              <span className="w-10 text-center text-sm font-semibold text-zinc-900 bg-zinc-100 rounded-lg py-1">
                {form.num_questions}
              </span>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 rounded-xl hover:bg-zinc-100 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2 text-sm font-semibold bg-zinc-900 text-white rounded-xl hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading && (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {loading ? "Génération…" : "Générer"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Exercise Card ───────────────────────────────────────────────────────────

function ExerciseCard({
  exercise,
  onClick,
}: {
  exercise: Exercise;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left group bg-white border border-zinc-200 rounded-2xl p-5 hover:border-zinc-300 hover:shadow-md transition-all duration-200"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-zinc-900 truncate group-hover:text-zinc-700 transition-colors">
            {exercise.title}
          </h3>
          <p className="text-sm text-zinc-400 mt-1">{formatDate(exercise.created_at)}</p>
        </div>
        <span
          className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full border ${MODE_COLORS[exercise.mode]}`}
        >
          {MODE_LABELS[exercise.mode]}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_COLORS[exercise.status]}`}
          >
            {STATUS_LABELS[exercise.status]}
          </span>
          <span className="text-xs text-zinc-400">
            {exercise.questions.length} question
            {exercise.questions.length !== 1 ? "s" : ""}
          </span>
        </div>

        {exercise.total_score !== null && (
          <span className="text-sm font-bold text-zinc-900">
            {exercise.total_score}%
          </span>
        )}
      </div>
    </button>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function ExercisesPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [exerciseList, setExerciseList] = useState<Exercise[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setLoading(true);
    exercisesApi
      .list(sessionId)
      .then(({ exercises, total }) => {
        setExerciseList(exercises);
        setTotal(total);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Erreur de chargement.")
      )
      .finally(() => setLoading(false));
  }, [sessionId]);

  function handleCreated(exercise: Exercise) {
    setExerciseList((prev) => [exercise, ...prev]);
    setTotal((t) => t + 1);
    setShowModal(false);
    router.push(`/sessions/${sessionId}/exercises/${exercise.id}`);
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <div className="max-w-3xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">Exercices</h1>
            {!loading && (
              <p className="text-sm text-zinc-400 mt-1">
                {total} exercice{total !== 1 ? "s" : ""} au total
              </p>
            )}
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-zinc-900 text-white text-sm font-semibold rounded-xl hover:bg-zinc-700 transition-colors shadow-sm"
          >
            <span className="text-lg leading-none">+</span>
            Nouvel exercice
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-28 rounded-2xl bg-zinc-200 animate-pulse"
              />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-16 text-red-500 bg-red-50 border border-red-100 rounded-2xl">
            {error}
          </div>
        ) : exerciseList.length === 0 ? (
          <div className="text-center py-20 border-2 border-dashed border-zinc-200 rounded-2xl">
            <p className="text-zinc-400 text-sm">Aucun exercice pour cette session.</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 text-sm font-medium text-zinc-900 underline underline-offset-2 hover:no-underline"
            >
              Créer le premier
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {exerciseList.map((ex) => (
              <ExerciseCard
                key={ex.id}
                exercise={ex}
                onClick={() =>
                  router.push(`/sessions/${sessionId}/exercises/${ex.id}`)
                }
              />
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <CreateModal
          sessionId={sessionId}
          onClose={() => setShowModal(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
