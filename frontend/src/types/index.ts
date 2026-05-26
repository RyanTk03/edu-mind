// ═══════════════════════════════════════════════════════════════════════════════
// API Types - Matching backend schemas
// ═══════════════════════════════════════════════════════════════════════════════

// Auth
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  level: "débutant" | "intermédiaire" | "avancé";
  level_score: number | null;  // null = not assessed yet
  exercises_completed: number;
  weak_points: string[];
  strong_points: string[];
  preferences: Record<string, unknown>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

// Sessions
export interface Session {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  attachment_count?: number;
  message_count?: number;
  exercise_count?: number;
  // Per-session progress
  progress_score?: number | null;  // null = no exercises completed
  exercises_completed?: number;
}

export interface SessionCreate {
  title: string;
  description?: string;
}

// Messages
export type MessageRole = "user" | "ai";

export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  metadata: {
    intent?: "question" | "exercise" | "answer";
    has_exercise?: boolean;
  };
}

export interface ChatHistory {
  messages: Message[];
  total: number;
}

// Attachments
export interface Attachment {
  id: string;
  session_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  is_processed: boolean;
  chunk_count: number;
  processing_error: string | null;
}

// Exercises
export type QuestionType = "qcm" | "open" | "code";
export type ExerciseMode = "evaluation" | "reinforcement" | "free";
export type ExerciseStatus = "pending" | "in_progress" | "completed";

export interface QuestionOption {
  label: string;
  text: string;
}

export interface Question {
  order: number;
  type: QuestionType;
  question_text: string;
  options: QuestionOption[];
  user_answer: string | null;
  is_correct: boolean | null;
  correct_answer?: string;
  gap_analysis?: string;
}

export interface Exercise {
  id: string;
  session_id: string;
  title: string;
  mode: ExerciseMode;
  status: ExerciseStatus;
  questions: Question[];
  total_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface ExerciseGenerateRequest {
  mode: ExerciseMode;
  title?: string;
  num_questions?: number;
}

export interface AnswerSubmission {
  question_order: number;
  answer: string;
}

export interface ExerciseSubmitRequest {
  answers: AnswerSubmission[];
}

// API Responses
export interface ApiError {
  detail: string;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

export interface ExerciseListResponse {
  exercises: Exercise[];
  total: number;
}
