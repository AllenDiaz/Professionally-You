"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAdminToken } from "@/components/admin/AdminShell";
import { getConversations, type ConversationOut } from "@/lib/api";

export default function ConversationsPage() {
  const token = useAdminToken();
  const [conversations, setConversations] = useState<ConversationOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConversations(token)
      .then(setConversations)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load conversations"));
  }, [token]);

  return (
    <div>
      <h1 className="mb-4 font-mono text-xs tracking-[0.2em] text-ink-muted">CONVERSATIONS</h1>
      {error && <p className="font-mono text-xs text-signal">{error}</p>}
      {!error && conversations === null && <p className="font-mono text-xs text-ink-muted">loading…</p>}
      {conversations !== null && conversations.length === 0 && (
        <p className="font-serif text-ink-muted">No conversations yet.</p>
      )}
      {conversations !== null && conversations.length > 0 && (
        <ul className="divide-y divide-rule">
          {conversations.map((c) => (
            <li key={c.id} className="py-3">
              <Link
                href={`/admin/conversations/${c.id}`}
                className="font-mono text-sm text-ink hover:text-phosphor"
              >
                #{c.id}
              </Link>
              <span className="ml-3 font-mono text-[11px] text-ink-muted">
                {new Date(c.created_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
