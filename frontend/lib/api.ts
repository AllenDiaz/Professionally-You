// Typed client for the FastAPI backend. Calls are made directly from the
// browser (the backend's CORS config allows this origin) — no Next.js API
// routes needed as a proxy.

export type ChatRole = "system" | "user" | "assistant" | "tool";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatResponse {
  reply: string;
  conversation_id: number;
}

export interface ProfileSection {
  title: string;
  content: string;
}

export interface Profile {
  name: string;
  headline: string;
  summary: string;
  sections: ProfileSection[];
}

export interface LeadOut {
  id: number;
  email: string;
  name: string | null;
  notes: string | null;
  conversation_id: number | null;
  created_at: string;
}

export interface UnknownQuestionOut {
  id: number;
  question: string;
  conversation_id: number | null;
  created_at: string;
}

export interface MessageOut {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface ConversationOut {
  id: number;
  created_at: string;
}

export interface ConversationDetail extends ConversationOut {
  messages: MessageOut[];
}

export interface HealthResponse {
  status: string;
  vertex_configured: boolean;
  pushover_configured: boolean;
  model: string;
}

export type StreamEvent =
  | { delta: string }
  | { error: string }
  | { done: true; conversation_id: number };

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? body.error ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json() as Promise<T>;
}

export function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  conversationId?: number
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, history, conversation_id: conversationId }),
  });
}

/** Stream a chat reply over SSE, yielding one parsed event per server frame. */
export async function* streamChat(
  message: string,
  history: ChatMessage[] = [],
  conversationId?: number,
  signal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${apiBase()}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, conversation_id: conversationId }),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const line = frame.split("\n").find((l) => l.startsWith("data: "));
      if (line) {
        yield JSON.parse(line.slice("data: ".length)) as StreamEvent;
      }
    }
  }
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export function getProfile(): Promise<Profile> {
  return request<Profile>("/api/profile");
}

export function updateProfile(token: string, profile: Profile): Promise<Profile> {
  return request<Profile>("/api/profile", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(profile),
  });
}

export function reindexProfile(token: string): Promise<{ chunks: number }> {
  return request<{ chunks: number }>("/api/profile/reindex", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

function adminRequest<T>(token: string, path: string): Promise<T> {
  return request<T>(path, { headers: { Authorization: `Bearer ${token}` } });
}

export function getLeads(token: string): Promise<LeadOut[]> {
  return adminRequest<LeadOut[]>(token, "/api/admin/leads");
}

export function getUnknownQuestions(token: string): Promise<UnknownQuestionOut[]> {
  return adminRequest<UnknownQuestionOut[]>(token, "/api/admin/unknown-questions");
}

export function getConversations(token: string): Promise<ConversationOut[]> {
  return adminRequest<ConversationOut[]>(token, "/api/admin/conversations");
}

export function getConversation(token: string, id: number): Promise<ConversationDetail> {
  return adminRequest<ConversationDetail>(token, `/api/admin/conversations/${id}`);
}
