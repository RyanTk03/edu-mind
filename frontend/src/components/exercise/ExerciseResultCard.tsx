"use client";

import { useState } from "react";
import { Card, Badge } from "@/components/ui";
import type { CorrectionResult, InlineExerciseData, CorrectedQuestion } from "@/types";

interface ExerciseResultCardProps {
  result: CorrectionResult;
  exercise: InlineExerciseData;
}

function QuestionResult({ question, index }: { question: CorrectedQuestion; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`rounded-lg border p-3 ${
        question.is_correct
          ? "border-green-200 bg-green-50/50"
          : "border-red-200 bg-red-50/50"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-sm font-semibold ${
                question.is_correct
                  ? "bg-green-500 text-white"
                  : "bg-red-500 text-white"
              }`}
            >
              {question.is_correct ? "✓" : "✗"}
            </span>
            <span className="text-sm font-medium text-gray-700">
              Q{question.order || index + 1}
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-800">
            {question.question_text?.slice(0, 100)}
            {question.question_text && question.question_text.length > 100 && "..."}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 text-sm">
          <span className={question.is_correct ? "text-green-700" : "text-red-700"}>
            {question.student_answer || "-"}
          </span>
          {!question.is_correct && (
            <span className="text-green-600 font-medium">
              → {question.correct_answer}
            </span>
          )}
        </div>
      </div>

      {/* Expandable feedback */}
      {(question.gap_analysis || question.feedback || question.explanation) && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs text-blue-600 hover:underline"
          >
            {expanded ? "Masquer les détails" : "Voir les détails"}
          </button>
          {expanded && (
            <div className="mt-2 space-y-2 border-t border-gray-200 pt-2">
              {question.feedback && (
                <p className="text-sm text-gray-700">{question.feedback}</p>
              )}
              {question.gap_analysis && (
                <p className="text-sm text-orange-700">
                  <strong>Analyse :</strong> {question.gap_analysis}
                </p>
              )}
              {question.explanation && (
                <p className="text-sm text-blue-700">
                  <strong>Explication :</strong> {question.explanation}
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function ExerciseResultCard({ result, exercise }: ExerciseResultCardProps) {
  const isQCM = exercise.type === "qcm" && result.corrected_questions;
  const scorePercent = isQCM && result.total_questions
    ? Math.round((result.correct_count || 0) / result.total_questions * 100)
    : Math.round(result.score * 100);
  const isGood = scorePercent >= 70;
  const isMedium = scorePercent >= 40 && scorePercent < 70;

  return (
    <Card className="w-full max-w-[85%] overflow-hidden border border-gray-200 shadow-sm">
      {/* Header with score */}
      <div
        className={`px-5 py-5 ${
          isGood
            ? "bg-gradient-to-r from-green-50 to-green-100/50 border-b border-green-200"
            : isMedium
            ? "bg-gradient-to-r from-yellow-50 to-yellow-100/50 border-b border-yellow-200"
            : "bg-gradient-to-r from-red-50 to-red-100/50 border-b border-red-200"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {isGood ? "Excellent !" : isMedium ? "Pas mal !" : "Résultat"}
            </h3>
            <p className="mt-1 text-base text-gray-600">
              {exercise.topic || "Exercice"}
            </p>
            {isQCM && result.total_questions && (
              <p className="mt-1 text-sm text-gray-500">
                {result.correct_count || 0} / {result.total_questions} questions correctes
              </p>
            )}
          </div>
          <div className="flex flex-col items-center gap-1">
            <div
              className={`flex h-20 w-20 flex-col items-center justify-center rounded-full border-4 ${
                isGood
                  ? "border-green-500 bg-green-100 text-green-700"
                  : isMedium
                  ? "border-yellow-500 bg-yellow-100 text-yellow-700"
                  : "border-red-500 bg-red-100 text-red-700"
              }`}
            >
              <span className="text-2xl font-bold">{scorePercent}%</span>
            </div>
            {result.grade_letter && (
              <span
                className={`text-lg font-bold ${
                  isGood ? "text-green-700" : isMedium ? "text-yellow-700" : "text-red-700"
                }`}
              >
                {result.grade_letter}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white p-5 space-y-5">
        {/* QCM: Individual question results */}
        {isQCM && result.corrected_questions && result.corrected_questions.length > 0 && (
          <div>
            <h4 className="mb-3 text-base font-semibold text-gray-700">
              Détail par question
            </h4>
            <div className="space-y-2">
              {result.corrected_questions.map((q, idx) => (
                <QuestionResult key={q.order || idx} question={q} index={idx} />
              ))}
            </div>
          </div>
        )}

        {/* Strong points */}
        {result.strong_points && result.strong_points.length > 0 && (
          <div>
            <h4 className="mb-3 text-base font-semibold text-green-700">
              Points forts
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.strong_points.map((point, idx) => (
                <Badge key={idx} variant="success" className="text-sm px-3 py-1">
                  {point}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Errors / Weak points */}
        {result.errors && result.errors.length > 0 && (
          <div>
            <h4 className="mb-3 text-base font-semibold text-orange-700">
              Points à retravailler
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.errors.map((error, idx) => (
                <Badge key={idx} variant="warning" className="text-sm px-3 py-1">
                  {error}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Feedback hints */}
        {result.feedback_hints && result.feedback_hints.length > 0 && (
          <div>
            <h4 className="mb-3 text-base font-semibold text-blue-700">
              Conseils
            </h4>
            <ul className="space-y-2 rounded-xl bg-blue-50 p-4 text-base text-blue-800 border border-blue-100">
              {result.feedback_hints.map((hint, idx) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-blue-400">💡</span>
                  <span>{hint}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Summary */}
        {result.summary && (
          <div className="rounded-xl bg-gray-50 p-4 text-base text-gray-700 border border-gray-200">
            {result.summary}
          </div>
        )}

        {/* Verdict message */}
        <div
          className={`rounded-xl p-4 text-base font-medium ${
            isGood
              ? "bg-green-50 text-green-800 border border-green-200"
              : isMedium
              ? "bg-yellow-50 text-yellow-800 border border-yellow-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          {isGood
            ? "Excellent travail ! Continuez comme ça !"
            : isMedium
            ? "Bon effort ! Revoyez les points mentionnés ci-dessus."
            : "Ne vous découragez pas ! Revoyez les concepts et réessayez."}
        </div>
      </div>
    </Card>
  );
}
