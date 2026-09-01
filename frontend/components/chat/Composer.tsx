"use client";

import type { KeyboardEvent } from "react";

interface ComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function Composer({ value, onChange, onSubmit, disabled }: ComposerProps) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  }

  return (
    <div className="border-t border-rule bg-paper">
      <div className="mx-auto flex max-w-2xl items-center gap-2 px-4 py-3 sm:px-6">
        <span className="font-mono text-sm text-phosphor" aria-hidden>
          %
        </span>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="ask allen something…"
          aria-label="Message"
          className="flex-1 bg-transparent font-mono text-sm text-ink outline-none placeholder:text-ink-muted/60 disabled:opacity-50"
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          className="hidden shrink-0 font-mono text-[11px] text-ink-muted transition-colors hover:text-phosphor disabled:opacity-40 sm:inline"
          aria-label="Send message"
        >
          [enter &#8629;]
        </button>
      </div>
    </div>
  );
}
