"use client";

import { useState } from "react";
import { Card, Button } from "@/components/ui";
import type { InlineExerciseData } from "@/types";

interface CodeExerciseCardProps {
  exercise: InlineExerciseData;
  onSubmit: (code: string) => void;
  isLoading?: boolean;
}

export function CodeExerciseCard({ exercise, onSubmit, isLoading = false }: CodeExerciseCardProps) {
  const [code, setCode] = useState("");
  const [showHints, setShowHints] = useState(false);

  const handleSubmit = () => {
    if (code.trim()) {
      onSubmit(code.trim());
    }
  };

  const difficultyLabel = exercise.difficulty === "easy" ? "Facile" : exercise.difficulty === "medium" ? "Intermédiaire" : "Difficile";
  const difficultyColor = exercise.difficulty === "easy" ? "text-green-700 bg-green-50 border-green-300" : exercise.difficulty === "medium" ? "text-blue-700 bg-blue-50 border-blue-300" : "text-orange-700 bg-orange-50 border-orange-300";

  return (
    <Card className="w-full max-w-[85%] overflow-hidden border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800 px-5 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">
            💻 {exercise.topic || "Exercice de code"}
          </h3>
          {exercise.difficulty && (
            <span className={`rounded-full px-3 py-1 text-sm font-semibold border ${difficultyColor}`}>
              {difficultyLabel}
            </span>
          )}
        </div>
      </div>

      {/* Question */}
      <div className="border-b border-gray-200 bg-white p-5">
        <p className="text-base leading-relaxed text-gray-900 whitespace-pre-wrap">
          {exercise.question}
        </p>

        {/* Hints */}
        {exercise.hints && exercise.hints.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowHints(!showHints)}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
            >
              {showHints ? "Masquer les indices" : "💡 Voir les indices"}
            </button>
            {showHints && (
              <ul className="mt-3 space-y-2 rounded-xl bg-blue-50 p-4 text-base text-blue-800 border border-blue-100">
                {exercise.hints.map((hint, idx) => (
                  <li key={idx} className="flex gap-2">
                    <span className="text-blue-400">•</span>
                    <span>{hint}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Code editor */}
      <div className="bg-gray-900 p-5">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="# Écrivez votre code ici..."
          rows={12}
          className="w-full resize-none rounded-xl border-2 border-gray-700 bg-gray-800 p-4 font-mono text-base text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          spellCheck={false}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-5 py-4">
        <span className="text-sm text-gray-500">
          {code.split("\n").length} lignes
        </span>
        <Button
          onClick={handleSubmit}
          disabled={!code.trim()}
          isLoading={isLoading}
        >
          Soumettre le code
        </Button>
      </div>
    </Card>
  );
}
