"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import { formatRelativeTime, getLevelColor, getLevelLabel } from "@/lib/utils";
import { Header } from "@/components/layout";
import { Button, Card, Input, Progress } from "@/components/ui";
import type { Session } from "@/types";

export default function SessionsPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const data = await api.sessions.list();
        setSessions(data.sessions);
      } catch (error) {
        console.error("Failed to load sessions:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  const createSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setIsCreating(true);
    try {
      const session = await api.sessions.create({ title: newTitle.trim() });
      router.push(`/sessions/${session.id}`);
    } catch (error) {
      console.error("Failed to create session:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const deleteSession = async (id: string) => {
    if (!confirm("Supprimer cette session ?")) return;

    try {
      await api.sessions.delete(id);
      setSessions(sessions.filter((s) => s.id !== id));
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />

      <main className="flex-1 px-4 py-8">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Mes Sessions</h1>
              <p className="text-gray-600">
                Gérez vos sessions d&apos;apprentissage
              </p>
            </div>

            <Button onClick={() => setShowNewForm(true)}>
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Nouvelle session
            </Button>
          </div>

          {showNewForm && (
            <Card className="mb-6">
              <form onSubmit={createSession} className="flex gap-3 p-4">
                <Input
                  placeholder="Nom de la session (ex: Mathématiques - Dérivées)"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="flex-1"
                  autoFocus
                />
                <Button type="submit" isLoading={isCreating}>
                  Créer
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setShowNewForm(false);
                    setNewTitle("");
                  }}
                >
                  Annuler
                </Button>
              </form>
            </Card>
          )}

          {isLoading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : sessions.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <svg
                  className="h-8 w-8 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </div>
              <h3 className="mb-2 text-lg font-semibold text-gray-900">
                Aucune session
              </h3>
              <p className="mb-6 text-gray-600">
                Créez votre première session pour commencer à apprendre
              </p>
              <Button onClick={() => setShowNewForm(true)}>
                Créer une session
              </Button>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {sessions.map((session) => (
                <Link key={session.id} href={`/sessions/${session.id}`}>
                  <Card className="group h-full cursor-pointer p-5 transition-shadow hover:shadow-md">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="mb-1 font-semibold text-gray-900 group-hover:text-blue-600">
                          {session.title}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {formatRelativeTime(session.updated_at)}
                        </p>
                      </div>

                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="rounded p-1 text-gray-400 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>

                    {/* Per-session progress */}
                    {(session.exercises_completed ?? 0) > 0 && (
                      <div className="mt-3 flex items-center gap-2">
                        <Progress
                          value={(session.progress_score ?? 0) * 100}
                          className="h-1.5 flex-1"
                          indicatorClassName={
                            (session.progress_score ?? 0) < 0.35
                              ? "bg-orange-500"
                              : (session.progress_score ?? 0) < 0.65
                              ? "bg-blue-500"
                              : "bg-green-500"
                          }
                        />
                        <span className="text-xs font-medium text-gray-600">
                          {Math.round((session.progress_score ?? 0) * 100)}%
                        </span>
                      </div>
                    )}

                    <div className="mt-1 items-center gap-2 sm:flex">
                      <span className="text-sm text-gray-500">Niveau:</span>
                      <span className={`text-sm font-medium ${getLevelColor(session.level_score)}`}>
                        {getLevelLabel(session.level_score)}
                      </span>
                    </div>

                    <div className="mt-3 flex gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <svg
                          className="h-3.5 w-3.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                          />
                        </svg>
                        {session.message_count || 0} messages
                      </span>
                      <span className="flex items-center gap-1">
                        <svg
                          className="h-3.5 w-3.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        {session.attachment_count || 0} fichiers
                      </span>
                      {(session.exercises_completed ?? 0) > 0 && (
                        <span className="flex items-center gap-1">
                          <svg
                            className="h-3.5 w-3.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                            />
                          </svg>
                          {session.exercises_completed} exercice{(session.exercises_completed ?? 0) > 1 ? "s" : ""}
                        </span>
                      )}
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
