"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import { formatRelativeTime, formatFileSize } from "@/lib/utils";
import { Button, Card, Textarea, Badge } from "@/components/ui";
import type { Session, Message, Attachment } from "@/types";

export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"chat" | "files">("chat");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && sessionId) {
      loadSessionData();
    }
  }, [isAuthenticated, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Poll for attachment processing status
  useEffect(() => {
    const unprocessedAttachments = attachments.filter((a) => !a.is_processed);
    if (unprocessedAttachments.length === 0) return;

    const pollInterval = setInterval(async () => {
      for (const attachment of unprocessedAttachments) {
        try {
          const status = await api.attachments.getStatus(sessionId, attachment.id);
          if (status.is_processed || status.processing_error) {
            setAttachments((prev) =>
              prev.map((a) =>
                a.id === attachment.id
                  ? {
                      ...a,
                      is_processed: status.is_processed,
                      chunk_count: status.chunk_count,
                      processing_error: status.processing_error,
                    }
                  : a
              )
            );
          }
        } catch (error) {
          console.error("Failed to poll attachment status:", error);
        }
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [attachments, sessionId]);

  const loadSessionData = async () => {
    try {
      const [sessionData, chatData, attachmentsData] = await Promise.all([
        api.sessions.get(sessionId),
        api.chat.getHistory(sessionId),
        api.attachments.list(sessionId),
      ]);
      setSession(sessionData);
      setMessages(chatData.messages);
      setAttachments(attachmentsData);
    } catch (error) {
      console.error("Failed to load session:", error);
      router.push("/sessions");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isSending) return;

    const content = newMessage.trim();
    setNewMessage("");
    setIsSending(true);

    // Optimistic update - add user message immediately
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
      metadata: {},
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const aiMessage = await api.chat.sendMessage(sessionId, content);
      // Replace temp message and add AI response
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMessage.id),
        { ...tempUserMessage, id: `user-${Date.now()}` },
        aiMessage,
      ]);
    } catch (error) {
      console.error("Failed to send message:", error);
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
      setNewMessage(content);
    } finally {
      setIsSending(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const attachment = await api.attachments.upload(sessionId, file);
      setAttachments((prev) => [...prev, attachment]);
    } catch (error) {
      console.error("Failed to upload file:", error);
      alert("Erreur lors de l'upload du fichier");
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const deleteAttachment = async (attachmentId: string) => {
    if (!confirm("Supprimer ce fichier ?")) return;

    try {
      await api.attachments.delete(sessionId, attachmentId);
      setAttachments((prev) => prev.filter((a) => a.id !== attachmentId));
    } catch (error) {
      console.error("Failed to delete attachment:", error);
    }
  };

  if (authLoading || !isAuthenticated || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex items-center gap-3">
          <Link
            href="/sessions"
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </Link>
          <h1 className="font-semibold text-gray-900">{session?.title}</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("chat")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => setActiveTab("files")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "files"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Fichiers
            {attachments.length > 0 && (
              <span className="rounded-full bg-gray-200 px-1.5 py-0.5 text-xs">
                {attachments.length}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {activeTab === "chat" ? (
          <div className="flex flex-1 flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mx-auto max-w-3xl space-y-4">
                {messages.length === 0 ? (
                  <div className="py-12 text-center">
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
                          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                        />
                      </svg>
                    </div>
                    <h3 className="mb-2 text-lg font-semibold text-gray-900">
                      Commencez la conversation
                    </h3>
                    <p className="text-gray-600">
                      Posez une question, demandez un exercice ou uploadez un
                      document
                    </p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 bg-white p-4">
              <form
                onSubmit={sendMessage}
                className="mx-auto flex max-w-3xl gap-3"
              >
                <Textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Posez une question, demandez un exercice..."
                  className="min-h-[44px] max-h-32 resize-none"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage(e);
                    }
                  }}
                />
                <Button type="submit" isLoading={isSending} disabled={!newMessage.trim()}>
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
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </Button>
              </form>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="mx-auto max-w-3xl">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">Documents</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
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
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                    />
                  </svg>
                  Upload
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>

              {attachments.length === 0 ? (
                <Card className="p-8 text-center">
                  <p className="text-gray-600">
                    Aucun fichier. Uploadez des documents (PDF, TXT) pour
                    enrichir le contexte de l&apos;IA.
                  </p>
                </Card>
              ) : (
                <div className="space-y-2">
                  {attachments.map((attachment) => (
                    <Card
                      key={attachment.id}
                      className="flex items-center justify-between p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                          <svg
                            className="h-5 w-5 text-blue-600"
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
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">
                            {attachment.original_filename}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(attachment.file_size)} •{" "}
                            {formatRelativeTime(attachment.uploaded_at)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {attachment.processing_error ? (
                          <Badge variant="destructive" title={attachment.processing_error}>
                            Erreur
                          </Badge>
                        ) : attachment.is_processed ? (
                          <Badge variant="success">
                            Traité ({attachment.chunk_count} chunks)
                          </Badge>
                        ) : (
                          <Badge variant="warning">En cours...</Badge>
                        )}
                        <button
                          onClick={() => deleteAttachment(attachment.id)}
                          className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
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
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white text-gray-900 shadow-sm border border-gray-200"
        }`}
      >
        {isUser ? (
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div className="message-content text-sm">
            <ReactMarkdown
              components={{
                // Customize heading styles
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2 mt-3">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2 mt-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-1 mt-2">{children}</h3>,
                // Lists
                ul: ({ children }) => <ul className="list-disc ml-5 mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal ml-5 mb-2">{children}</ol>,
                li: ({ children }) => <li className="mb-0.5">{children}</li>,
                // Code blocks
                pre: ({ children }) => (
                  <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg mb-2 overflow-x-auto text-xs font-mono">
                    {children}
                  </pre>
                ),
                code: ({ className, children }) => {
                  const isBlock = className?.includes("language-");
                  return isBlock ? (
                    <code className={`${className} text-gray-100`}>{children}</code>
                  ) : (
                    <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-xs font-mono">
                      {children}
                    </code>
                  );
                },
                // Paragraphs
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                // Strong/Bold
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                // Emphasis/Italic
                em: ({ children }) => <em className="italic">{children}</em>,
                // Links
                a: ({ href, children }) => (
                  <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
                // Blockquotes
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-gray-300 pl-3 italic text-gray-600 my-2">
                    {children}
                  </blockquote>
                ),
                // Horizontal rule
                hr: () => <hr className="my-3 border-gray-200" />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        <p
          className={`mt-2 text-xs ${
            isUser ? "text-blue-200" : "text-gray-400"
          }`}
        >
          {formatRelativeTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
