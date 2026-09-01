"use client";

import { useEffect, useState } from "react";

const PHRASES = [
  "querying career index…",
  "checking the linkedin graph…",
  "drafting reply…",
];

/** A single-line, honest status cycle — not three bouncing dots. */
export function TypingIndicator() {
  const [phrase, setPhrase] = useState(PHRASES[0]);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      // One-time hydration-safe read of a browser-only API — freezes the
      // cycling copy to a single static phrase instead of animating it.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPhrase("thinking…");
      return;
    }
    let index = 0;
    const id = setInterval(() => {
      index = (index + 1) % PHRASES.length;
      setPhrase(PHRASES[index]);
    }, 900);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="py-5">
      <div className="mb-1.5 font-mono text-xs tracking-wide text-phosphor">
        allen <span className="text-rule">&#8250;</span>
      </div>
      <div className="font-mono text-xs text-ink-muted" aria-live="polite">
        {phrase}
      </div>
    </div>
  );
}
