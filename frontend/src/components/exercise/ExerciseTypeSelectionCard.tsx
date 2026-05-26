"use client";

import { Card } from "@/components/ui";
import type { InlineExerciseType } from "@/types";

const EXERCISE_TYPES = [
  {
    type: "qcm" as InlineExerciseType,
    icon: "📋",
    label: "QCM",
    description: "Quiz à choix multiples",
    color: "hover:border-purple-400 hover:bg-purple-50",
  },
  {
    type: "code" as InlineExerciseType,
    icon: "💻",
    label: "Code",
    description: "Exercice de programmation",
    color: "hover:border-emerald-400 hover:bg-emerald-50",
  },
  {
    type: "open" as InlineExerciseType,
    icon: "📝",
    label: "Question ouverte",
    description: "Réponse libre",
    color: "hover:border-blue-400 hover:bg-blue-50",
  },
];

interface ExerciseTypeSelectionCardProps {
  onSelect: (type: InlineExerciseType, topic: string) => void;
}

export function ExerciseTypeSelectionCard({ onSelect }: ExerciseTypeSelectionCardProps) {
  const handleSelect = (type: InlineExerciseType) => {
    // For now, just send a message requesting this type
    // The user will specify the topic in their message
    const typeLabels = {
      qcm: "un QCM",
      code: "un exercice de code",
      open: "une question ouverte",
    };
    onSelect(type, typeLabels[type]);
  };

  return (
    <Card className="w-full max-w-[85%] overflow-hidden border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-5 py-4">
        <h3 className="text-base font-semibold text-gray-900">
          Quel type d'exercice souhaitez-vous ?
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Choisissez un type, puis précisez le sujet
        </p>
      </div>

      {/* Type Options */}
      <div className="bg-white p-5">
        <div className="grid gap-3">
          {EXERCISE_TYPES.map((item) => (
            <button
              key={item.type}
              onClick={() => handleSelect(item.type)}
              className={`flex items-center gap-4 rounded-xl border-2 border-gray-200 p-4 text-left transition-all ${item.color}`}
            >
              <span className="text-3xl">{item.icon}</span>
              <div>
                <div className="text-base font-semibold text-gray-900">{item.label}</div>
                <div className="text-sm text-gray-500">{item.description}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Footer hint */}
      <div className="border-t border-gray-200 bg-gray-50 px-5 py-3">
        <p className="text-sm text-gray-500 text-center">
          Ou tapez directement votre demande, ex: "QCM sur les matrices"
        </p>
      </div>
    </Card>
  );
}
