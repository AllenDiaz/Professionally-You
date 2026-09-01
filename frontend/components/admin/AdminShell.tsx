"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, getLeads } from "@/lib/api";

const AdminTokenContext = createContext<string | null>(null);

export function useAdminToken(): string {
  const token = useContext(AdminTokenContext);
  if (!token) throw new Error("useAdminToken used outside an authenticated AdminShell");
  return token;
}

const NAV = [
  { href: "/admin/leads", label: "leads" },
  { href: "/admin/questions", label: "unknown questions" },
  { href: "/admin/conversations", label: "conversations" },
  { href: "/admin/profile", label: "profile" },
];

export function AdminShell({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    // One-time hydration-safe read of a browser-only API; there is no
    // external-store event to subscribe to for a value we only ever change
    // ourselves (signOut / TokenGate), so a one-off mount read is correct.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setToken(sessionStorage.getItem("admin_token"));
    setReady(true);
  }, []);

  function signOut() {
    sessionStorage.removeItem("admin_token");
    setToken(null);
  }

  if (!ready) return null;

  if (!token) {
    return <TokenGate onAuthenticated={setToken} />;
  }

  return (
    <AdminTokenContext.Provider value={token}>
      <div className="flex min-h-screen flex-col">
        <header className="border-b border-rule">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6">
            <Link href="/admin" className="font-mono text-xs font-bold tracking-[0.2em] text-ink">
              ADMIN
            </Link>
            <button
              type="button"
              onClick={signOut}
              className="font-mono text-[11px] uppercase tracking-wide text-ink-muted transition-colors hover:text-signal"
            >
              sign out
            </button>
          </div>
          <nav className="mx-auto flex max-w-4xl gap-4 px-4 pb-2 font-mono text-xs sm:px-6">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={
                  pathname === item.href
                    ? "text-phosphor"
                    : "text-ink-muted transition-colors hover:text-ink"
                }
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6 sm:px-6">{children}</main>
      </div>
    </AdminTokenContext.Provider>
  );
}

function TokenGate({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function submit() {
    const candidate = value.trim();
    if (!candidate) return;
    setChecking(true);
    setError(null);
    try {
      await getLeads(candidate);
      sessionStorage.setItem("admin_token", candidate);
      onAuthenticated(candidate);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reach the API.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <p className="mb-4 font-mono text-xs tracking-[0.2em] text-ink-muted">ADMIN ACCESS</p>
        <div className="flex items-center gap-2 border-b border-rule pb-2">
          <span className="font-mono text-sm text-phosphor" aria-hidden>
            %
          </span>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            type="password"
            placeholder="admin token"
            autoFocus
            className="flex-1 bg-transparent font-mono text-sm text-ink outline-none placeholder:text-ink-muted/60"
          />
        </div>
        {error && <p className="mt-2 font-mono text-xs text-signal">{error}</p>}
        <button
          type="button"
          onClick={submit}
          disabled={checking || !value.trim()}
          className="mt-4 font-mono text-xs text-ink-muted transition-colors hover:text-phosphor disabled:opacity-40"
        >
          {checking ? "checking…" : "[enter ↵]"}
        </button>
      </div>
    </div>
  );
}
