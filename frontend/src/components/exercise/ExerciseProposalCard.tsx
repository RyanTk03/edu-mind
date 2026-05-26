"use client";

import { useState } from "react";
import { Card, Button } from "@/components/ui";
import type { ExerciseProposal } from "@/types";

const TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  qcm: { label: "QCM (Quiz à choix multiples)", icon: "📋" },
  code: { label: "Exercice de code", icon: "💻" },
  open: { label: "Question ouverte", icon: "📝" },
};

const DIFFICULTY_OPTIONS = [
  { value: "easy", label: "Facile", color: "text-green-700 bg-green-50 border-green-300", selectedColor: "text-green-700 bg-green-100 border-green-500 ring-2 ring-green-200" },
  { value: "medium", label: "Intermédiaire", color: "text-blue-700 bg-blue-50 border-blue-300", selectedColor: "text-blue-700 bg-blue-100 border-blue-500 ring-2 ring-blue-200" },
  { value: "hard", label: "Difficile", color: "text-orange-700 bg-orange-50 border-orange-300", selectedColor: "text-orange-700 bg-orange-100 border-orange-500 ring-2 ring-orange-200" },
];

const QUESTION_OPTIONS = [3, 5, 7, 10];

interface ExerciseProposalCardProps {
  proposal: ExerciseProposal;
  onConfirm: (modifiedProposal: ExerciseProposal) => void;
  onModify: () => void;
  isLoading?: boolean;
}

export function ExerciseProposalCard({
  proposal,
  onConfirm,
  onModify,
  isLoading = false,
}: ExerciseProposalCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedProposal, setEditedProposal] = useState<ExerciseProposal>(proposal);

  const typeInfo = TYPE_LABELS[proposal.type] || TYPE_LABELS.open;
  const currentDifficulty = DIFFICULTY_OPTIONS.find(d => d.value === editedProposal.difficulty) || DIFFICULTY_OPTIONS[1];

  const handleConfirm = () => {
    onConfirm(editedProposal);
  };

  const handleStartEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedProposal(proposal);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <Card className="w-full max-w-[85%] overflow-hidden border border-gray-200 shadow-sm">
        {/* Header */}
        <div className="border-b border-gray-200 bg-gray-50 px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{typeInfo.icon}</span>
            <h3 className="text-base font-semibold text-gray-900">Modifier l'exercice</h3>
          </div>
        </div>

        {/* Edit Form */}
        <div className="bg-white p-5 space-y-5">
          {/* Type (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">Type</label>
            <div className="text-base text-gray-900 bg-gray-100 rounded-xl px-4 py-3 border border-gray-200">
              {typeInfo.label}
            </div>
          </div>

          {/* Topic (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">Sujet</label>
            <div className="text-base text-gray-900 bg-gray-100 rounded-xl px-4 py-3 border border-gray-200">
              {proposal.topic}
            </div>
          </div>

          {/* Difficulty selector */}
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-3">Difficulté</label>
            <div className="flex gap-3">
              {DIFFICULTY_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setEditedProposal({ ...editedProposal, difficulty: option.value as "easy" | "medium" | "hard" })}
                  className={`flex-1 rounded-xl border-2 px-4 py-3 text-sm font-semibold transition-all ${
                    editedProposal.difficulty === option.value
                      ? option.selectedColor
                      : "text-gray-600 bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Number of questions (QCM only) */}
          {proposal.type === "qcm" && (
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-3">Nombre de questions</label>
              <div className="flex gap-3">
                {QUESTION_OPTIONS.map((num) => (
                  <button
                    key={num}
                    onClick={() => setEditedProposal({ ...editedProposal, num_questions: num })}
                    className={`flex-1 rounded-xl border-2 px-4 py-3 text-base font-semibold transition-all ${
                      editedProposal.num_questions === num
                        ? "text-blue-700 bg-blue-100 border-blue-500 ring-2 ring-blue-200"
                        : "text-gray-600 bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 border-t border-gray-200 bg-gray-50 px-5 py-4">
          <Button
            onClick={handleConfirm}
            isLoading={isLoading}
            className="flex-1"
          >
            Générer l'exercice
          </Button>
          <Button
            variant="outline"
            onClick={handleCancelEdit}
            disabled={isLoading}
          >
            Annuler
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-[85%] overflow-hidden border border-blue-200 bg-gradient-to-br from-blue-50/80 to-white shadow-sm">
      {/* Header */}
      <div className="border-b border-blue-100 bg-blue-50/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{typeInfo.icon}</span>
          <h3 className="text-base font-semibold text-gray-900">Exercice proposé</h3>
        </div>
      </div>

      {/* Details */}
      <div className="bg-white/80 p-5">
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-base text-gray-600">Type</span>
            <span className="text-base font-medium text-gray-900">{typeInfo.label}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-base text-gray-600">Sujet</span>
            <span className="text-base font-medium text-gray-900">{proposal.topic}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-base text-gray-600">Difficulté</span>
            <span className={`rounded-full px-3 py-1 text-sm font-semibold border ${currentDifficulty.color}`}>
              {currentDifficulty.label}
            </span>
          </div>
          {proposal.type === "qcm" && (
            <div className="flex items-center justify-between py-2">
              <span className="text-base text-gray-600">Questions</span>
              <span className="text-base font-semibold text-blue-600 bg-blue-100 rounded-full px-3 py-1">
                {editedProposal.num_questions}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 border-t border-blue-100 bg-blue-50/30 px-5 py-4">
        <Button
          onClick={handleConfirm}
          isLoading={isLoading}
          className="flex-1"
        >
          Générer l'exercice
        </Button>
        <Button
          variant="outline"
          onClick={handleStartEdit}
          disabled={isLoading}
        >
          Modifier
        </Button>
      </div>
    </Card>
  );
}
