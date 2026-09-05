const PROMPTS = [
  "tell me about your background",
  "what are the projects you already built?",
  "got a project you're proud of?",
  "what's your strengths and weaknesses?",
];

export function StarterPrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {PROMPTS.map((prompt) => (
        <button
          key={prompt}
          type="button"
          onClick={() => onSelect(prompt)}
          className="group flex items-center gap-2 rounded border border-rule px-3 py-2 text-left font-mono text-[13px] text-ink-muted transition-colors hover:border-phosphor hover:bg-phosphor-soft hover:text-ink"
        >
          <span className="text-phosphor">&gt;</span>
          <span>{prompt}</span>
        </button>
      ))}
    </div>
  );
}
