import { Prose } from "@/components/Prose";

interface MessageProps {
  role: "user" | "assistant";
  content: string;
  receipt?: string;
}

/** One turn in the session log — no bubbles, just a labeled line and a rule. */
export function Message({ role, content, receipt }: MessageProps) {
  const isUser = role === "user";

  return (
    <div className="border-b border-rule py-5 first:pt-0 last:border-b-0">
      <div className="mb-1.5 font-mono text-xs tracking-wide">
        <span className={isUser ? "text-ink-muted" : "text-phosphor"}>
          {isUser ? "you" : "allen"} <span className="text-rule">&#8250;</span>
        </span>
      </div>
      <div className="font-serif text-[15px] text-ink sm:text-base">
        <Prose content={content} />
      </div>
      {receipt && (
        <div className="mt-2 text-right font-mono text-[11px] text-ink-muted/70">
          [{receipt}]
        </div>
      )}
    </div>
  );
}
