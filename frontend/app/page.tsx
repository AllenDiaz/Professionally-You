"use client";

import { useEffect, useRef, useState } from "react";
import { Composer } from "@/components/chat/Composer";
import { Header } from "@/components/chat/Header";
import { Message } from "@/components/chat/Message";
import { StarterPrompts } from "@/components/chat/StarterPrompts";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { getHealth, streamChat, type ChatMessage } from "@/lib/api";

interface Turn {
  id: string;
  role: "user" | "assistant";
  content: string;
  receipt?: string;
}

let turnCounter = 0;
function nextId(): string {
  turnCounter += 1;
  return `t${turnCounter}`;
}

export default function ChatPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [modelName, setModelName] = useState<string | null>(null);
  const conversationIdRef = useRef<number | undefined>(undefined);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isStreaming = streamingContent !== null;

  useEffect(() => {
    getHealth()
      .then((health) => setModelName(health.model))
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, streamingContent]);

  async function send(message: string) {
    const trimmed = message.trim();
    if (!trimmed || isStreaming) return;

    const history: ChatMessage[] = turns.map((t) => ({ role: t.role, content: t.content }));
    setTurns((prev) => [...prev, { id: nextId(), role: "user", content: trimmed }]);
    setInput("");
    setStreamingContent("");

    let content = "";
    const startedAt = performance.now();

    try {
      for await (const event of streamChat(trimmed, history, conversationIdRef.current)) {
        if ("delta" in event) {
          content += event.delta;
          setStreamingContent(content);
        } else if ("done" in event) {
          conversationIdRef.current = event.conversation_id;
          const seconds = ((performance.now() - startedAt) / 1000).toFixed(1);
          const receipt = modelName ? `ok · ${seconds}s · ${modelName}` : `ok · ${seconds}s`;
          setTurns((prev) => [...prev, { id: nextId(), role: "assistant", content, receipt }]);
          setStreamingContent(null);
        } else if ("error" in event) {
          const fallback = content || "Something went wrong on my end. Try again?";
          setTurns((prev) => [...prev, { id: nextId(), role: "assistant", content: fallback }]);
          setStreamingContent(null);
        }
      }
    } catch {
      setTurns((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "assistant",
          content: "I couldn't reach the server. Check the API is running and try again.",
        },
      ]);
      setStreamingContent(null);
    }
  }

  const isEmpty = turns.length === 0 && streamingContent === null;

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 sm:px-6">
        {isEmpty ? (
          <div className="flex flex-1 flex-col justify-center gap-6 py-12">
            <p className="font-serif text-lg text-ink sm:text-xl">
              I&rsquo;m Allen — software engineer, data scientist, sometimes-cheese-refusenik.
              Ask about my work, or just say hi.
            </p>
            <StarterPrompts onSelect={send} />
          </div>
        ) : (
          <div className="flex-1 py-4">
            {turns.map((turn) => (
              <Message key={turn.id} role={turn.role} content={turn.content} receipt={turn.receipt} />
            ))}
            {streamingContent !== null &&
              (streamingContent === "" ? (
                <TypingIndicator />
              ) : (
                <Message role="assistant" content={streamingContent} />
              ))}
            <div ref={bottomRef} />
          </div>
        )}
      </main>
      <div className="mx-auto w-full max-w-2xl">
        <Composer value={input} onChange={setInput} onSubmit={() => send(input)} disabled={isStreaming} />
      </div>
    </div>
  );
}
