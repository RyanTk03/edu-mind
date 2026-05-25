"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { getLevelLabel, getLevelColor } from "@/lib/utils";
import { Header } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent, Avatar, Badge, Progress } from "@/components/ui";

export default function ProfilePage() {
  const { user, profile, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const levelScore = profile?.level_score ?? 0.5;
  const levelPercent = Math.round(levelScore * 100);

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />

      <main className="flex-1 px-4 py-8">
        <div className="mx-auto max-w-2xl">
          <h1 className="mb-8 text-2xl font-bold text-gray-900">Mon Profil</h1>

          {/* User Info */}
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <Avatar name={user?.name || "U"} size="lg" />
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {user?.name}
                  </h2>
                  <p className="text-gray-600">{user?.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Level Progress */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Niveau de progression</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex items-center justify-between">
                <span className={`text-2xl font-bold ${getLevelColor(levelScore)}`}>
                  {getLevelLabel(levelScore)}
                </span>
                <span className="text-lg font-medium text-gray-700">
                  {levelPercent}%
                </span>
              </div>

              <Progress
                value={levelPercent}
                className="h-3"
                indicatorClassName={
                  levelScore < 0.35
                    ? "bg-orange-500"
                    : levelScore < 0.65
                    ? "bg-blue-500"
                    : "bg-green-500"
                }
              />

              <div className="mt-4 flex justify-between text-sm text-gray-500">
                <span>Débutant</span>
                <span>Intermédiaire</span>
                <span>Avancé</span>
              </div>
            </CardContent>
          </Card>

          {/* Weak Points */}
          {profile?.weak_points && profile.weak_points.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Points à améliorer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {profile.weak_points.map((point, index) => (
                    <Badge key={index} variant="warning">
                      {point}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Strong Points */}
          {profile?.strong_points && profile.strong_points.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Points forts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {profile.strong_points.map((point, index) => (
                    <Badge key={index} variant="success">
                      {point}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Empty state if no weak/strong points */}
          {(!profile?.weak_points?.length && !profile?.strong_points?.length) && (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-gray-600">
                  Complétez des exercices pour découvrir vos points forts et axes d&apos;amélioration.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
