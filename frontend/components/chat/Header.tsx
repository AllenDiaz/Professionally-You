"use client";

import { useTheme } from "@/lib/useTheme";

export function Header() {
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-10 border-b border-rule bg-paper/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-baseline gap-2">
          <span
            className="inline-block h-1.5 w-1.5 rounded-full bg-phosphor"
            aria-hidden
          />
          <span className="font-mono text-xs font-bold tracking-[0.2em] text-ink">
            ALLEN DIAZ
          </span>
          <span className="hidden font-mono text-xs text-ink-muted sm:inline">
            / digital twin
          </span>
        </div>
        <button
          type="button"
          onClick={toggle}
          className="font-mono text-[11px] uppercase tracking-wide text-ink-muted transition-colors hover:text-phosphor"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? "light" : "dark"}
        </button>
      </div>
    </header>
  );
}
