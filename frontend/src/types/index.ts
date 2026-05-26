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
  level_score: number;
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

// ── QCM ───────────────────────────────────────────────────────────────────────

export type QCMDifficulty = "easy" | "medium" | "hard";
export type QCMStatus = "generated" | "submitted" | "evaluated";

export interface QCMOption {
  label: string;
  text: string;
}

export interface QCMQuestion {
  order: number;
  question_text: string;
  options: QCMOption[];
  correct_answer?: string;   // only exposed after evaluation
  explanation?: string;
  student_answer: string | null;
  is_correct: boolean | null;
  score: number | null;
  feedback: string | null;
  gap_analysis: string | null;
}

export interface QCMGradeReport {
  total_score: number;
  correct_count: number;
  total_questions: number;
  grade_letter: string;
  grade_label: string;
  strong_points: string[];
  weak_points: string[];
  recommendations: string[];
  summary: string;
}

export interface QCM {
  id: string;
  session_id: string;
  title: string;
  topic: string;
  difficulty: QCMDifficulty;
  status: QCMStatus;
  num_questions: number;
  questions: QCMQuestion[];
  grade_report: QCMGradeReport | null;
  created_at: string;
  submitted_at: string | null;
  evaluated_at: string | null;
}

export interface QCMGenerateRequest {
  topic: string;
  num_questions?: number;
  difficulty?: QCMDifficulty;
  title?: string;
}

export interface QCMAnswerItem {
  question_order: number;
  answer: string;
}

export interface QCMSubmitRequest {
  answers: QCMAnswerItem[];
}

export interface QCMListResponse {
  qcms: QCM[];
  total: number;
}

// Workflow graph visualization

export interface WorkflowNode {
  id: string;
  label: string;
  type: "start" | "agent" | "end";
  agent_type?: "retrieval" | "generation" | "correction" | "evaluation";
  description: string;
  inputs: string[];
  outputs: string[];
}

export interface WorkflowEdge {
  source: string;
  target: string;
  label: string;
  type: "direct" | "conditional";
}

export interface WorkflowGraph {
  workflow_name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  state_schema: Record<string, string>;
}
