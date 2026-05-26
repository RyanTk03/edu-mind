"use client";

import { useState } from "react";
import { Card, Button, Progress } from "@/components/ui";
import type { InlineExerciseData, QCMQuestion } from "@/types";

interface QCMCardProps {
  exercise: InlineExerciseData;
  onSubmit: (answers: string[]) => void;
  isLoading?: boolean;
}

export function QCMCard({ exercise, onSubmit, isLoading = false }: QCMCardProps) {
  const questions = exercise.questions || [];
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleSelect = (questionOrder: number, label: string) => {
    setAnswers((prev) => ({ ...prev, [questionOrder]: label }));
  };

  const handleSubmit = () => {
    const orderedAnswers = questions.map((q) => answers[q.order] || "");
    onSubmit(orderedAnswers);
  };

  const answeredCount = Object.keys(answers).length;
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;
  const canSubmit = answeredCount === questions.length;

  if (questions.length === 0) {
    return (
      <Card className="w-full max-w-[85%] p-5">
        <p className="text-base text-gray-600">Aucune question disponible.</p>
      </Card>
    );
  }

  const currentQuestion = questions[currentIndex];

  return (
    <Card className="w-full max-w-[85%] overflow-hidden border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-5 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900">
            {exercise.topic || "QCM"}
          </h3>
          <span className="text-sm font-medium text-gray-600">
            {answeredCount}/{questions.length} réponses
          </span>
        </div>
        <Progress value={progress} className="mt-3 h-2" />
      </div>

      {/* Question */}
      <div className="bg-white p-5">
        <div className="mb-4">
          <span className="inline-block rounded-md bg-blue-100 px-2.5 py-1 text-sm font-semibold text-blue-700">
            Question {currentQuestion.order}
          </span>
        </div>
        <p className="mb-5 text-base leading-relaxed text-gray-900">
          {currentQuestion.question_text}
        </p>

        {/* Options */}
        <div className="space-y-3">
          {currentQuestion.options.map((option) => {
            const isSelected = answers[currentQuestion.order] === option.label;
            return (
              <button
                key={option.label}
                onClick={() => handleSelect(currentQuestion.order, option.label)}
                className={`flex w-full items-center gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                  isSelected
                    ? "border-blue-500 bg-blue-50 shadow-sm"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <span
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-base font-bold ${
                    isSelected
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {option.label}
                </span>
                <span className={`text-base ${isSelected ? "text-blue-900 font-medium" : "text-gray-700"}`}>
                  {option.text}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-5 py-4">
        <div className="flex gap-1.5">
          {questions.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              className={`h-2.5 w-2.5 rounded-full transition-all ${
                idx === currentIndex
                  ? "bg-blue-500 scale-125"
                  : answers[questions[idx].order]
                  ? "bg-green-500"
                  : "bg-gray-300 hover:bg-gray-400"
              }`}
            />
          ))}
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
          >
            Précédent
          </Button>
          {currentIndex < questions.length - 1 ? (
            <Button
              size="sm"
              onClick={() => setCurrentIndex(currentIndex + 1)}
            >
              Suivant
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!canSubmit}
              isLoading={isLoading}
            >
              Soumettre ({answeredCount}/{questions.length})
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
