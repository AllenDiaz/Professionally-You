"use client";

import { useEffect, useState } from "react";
import { useAdminToken } from "@/components/admin/AdminShell";
import { getUnknownQuestions, type UnknownQuestionOut } from "@/lib/api";

export default function QuestionsPage() {
  const token = useAdminToken();
  const [questions, setQuestions] = useState<UnknownQuestionOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUnknownQuestions(token)
      .then(setQuestions)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load questions"));
  }, [token]);

  return (
    <div>
      <h1 className="mb-4 font-mono text-xs tracking-[0.2em] text-ink-muted">UNKNOWN QUESTIONS</h1>
      {error && <p className="font-mono text-xs text-signal">{error}</p>}
      {!error && questions === null && <p className="font-mono text-xs text-ink-muted">loading…</p>}
      {questions !== null && questions.length === 0 && (
        <p className="font-serif text-ink-muted">
          Nothing stumped Allen yet — unanswered questions will land here.
        </p>
      )}
      {questions !== null && questions.length > 0 && (
        <ul className="divide-y divide-rule">
          {questions.map((q) => (
            <li key={q.id} className="py-3">
              <p className="font-serif text-ink">{q.question}</p>
              <p className="mt-1 font-mono text-[11px] text-ink-muted">
                {new Date(q.created_at).toLocaleString()}
                {q.conversation_id != null && (
                  <>
                    {" · "}
                    <a
                      href={`/admin/conversations/${q.conversation_id}`}
                      className="text-phosphor underline underline-offset-2"
                    >
                      view conversation
                    </a>
                  </>
                )}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
