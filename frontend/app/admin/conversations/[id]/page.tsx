"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAdminToken } from "@/components/admin/AdminShell";
import { getConversation, type ConversationDetail } from "@/lib/api";

export default function ConversationDetailPage() {
  const params = useParams<{ id: string }>();
  const token = useAdminToken();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConversation(token, Number(params.id))
      .then(setConversation)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load conversation"));
  }, [token, params.id]);

  return (
    <div>
      <h1 className="mb-4 font-mono text-xs tracking-[0.2em] text-ink-muted">
        CONVERSATION #{params.id}
      </h1>
      {error && <p className="font-mono text-xs text-signal">{error}</p>}
      {!error && conversation === null && <p className="font-mono text-xs text-ink-muted">loading…</p>}
      {conversation &&
        conversation.messages.map((m) => (
          <div key={m.id} className="border-b border-rule py-4 last:border-b-0">
            <div className="mb-1 font-mono text-xs text-ink-muted">
              {m.role} · {new Date(m.created_at).toLocaleString()}
            </div>
            <p className="whitespace-pre-wrap font-serif text-ink">{m.content}</p>
          </div>
        ))}
    </div>
  );
}
