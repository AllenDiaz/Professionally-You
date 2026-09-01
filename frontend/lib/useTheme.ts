"use client";

import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

/** Reads/writes the `data-theme` attribute set by the inline script in layout.tsx. */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // One-time hydration-safe read: the inline script in layout.tsx already
    // set data-theme on the server-rendered <html> before this mounts.
    const current = document.documentElement.getAttribute("data-theme");
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(current === "dark" ? "dark" : "light");
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      return next;
    });
  }, []);

  return { theme, toggle };
}
