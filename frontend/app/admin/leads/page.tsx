"use client";

import { useEffect, useState } from "react";
import { useAdminToken } from "@/components/admin/AdminShell";
import { getLeads, type LeadOut } from "@/lib/api";

export default function LeadsPage() {
  const token = useAdminToken();
  const [leads, setLeads] = useState<LeadOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLeads(token)
      .then(setLeads)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load leads"));
  }, [token]);

  return (
    <div>
      <h1 className="mb-4 font-mono text-xs tracking-[0.2em] text-ink-muted">LEADS</h1>
      {error && <p className="font-mono text-xs text-signal">{error}</p>}
      {!error && leads === null && <p className="font-mono text-xs text-ink-muted">loading…</p>}
      {leads !== null && leads.length === 0 && (
        <p className="font-serif text-ink-muted">
          No one&rsquo;s left their email yet. When a visitor does, they&rsquo;ll show up here.
        </p>
      )}
      {leads !== null && leads.length > 0 && (
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-rule font-mono text-[11px] uppercase tracking-wide text-ink-muted">
              <th className="py-2 pr-4">email</th>
              <th className="py-2 pr-4">name</th>
              <th className="py-2 pr-4">notes</th>
              <th className="py-2">captured</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-b border-rule align-top">
                <td className="py-2 pr-4 font-mono text-xs">{lead.email}</td>
                <td className="py-2 pr-4 font-serif">{lead.name ?? "—"}</td>
                <td className="py-2 pr-4 font-serif text-ink-muted">{lead.notes ?? "—"}</td>
                <td className="py-2 font-mono text-xs text-ink-muted">
                  {new Date(lead.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
