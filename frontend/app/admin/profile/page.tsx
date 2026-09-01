"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useAdminToken } from "@/components/admin/AdminShell";
import { getProfile, reindexProfile, updateProfile, type Profile } from "@/lib/api";

export default function ProfilePage() {
  const token = useAdminToken();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profile"));
  }, []);

  async function save() {
    if (!profile) return;
    setSaving(true);
    setError(null);
    setStatus(null);
    try {
      setProfile(await updateProfile(token, profile));
      setStatus("saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function reindex() {
    setReindexing(true);
    setError(null);
    setStatus(null);
    try {
      const result = await reindexProfile(token);
      setStatus(`reindexed ${result.chunks} chunk${result.chunks === 1 ? "" : "s"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reindex");
    } finally {
      setReindexing(false);
    }
  }

  if (error && !profile) return <p className="font-mono text-xs text-signal">{error}</p>;
  if (!profile) return <p className="font-mono text-xs text-ink-muted">loading…</p>;

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="font-mono text-xs tracking-[0.2em] text-ink-muted">PROFILE</h1>

      <Field label="name">
        <input
          value={profile.name}
          onChange={(e) => setProfile({ ...profile, name: e.target.value })}
          className="w-full border-b border-rule bg-transparent py-1 font-serif text-ink outline-none focus:border-phosphor"
        />
      </Field>

      <Field label="headline">
        <input
          value={profile.headline}
          onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
          className="w-full border-b border-rule bg-transparent py-1 font-serif text-ink outline-none focus:border-phosphor"
        />
      </Field>

      <Field label="summary">
        <textarea
          value={profile.summary}
          onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
          rows={6}
          className="w-full resize-y border border-rule bg-panel p-2 font-serif text-ink outline-none focus:border-phosphor"
        />
      </Field>

      <div>
        <span className="mb-1 block font-mono text-[11px] uppercase tracking-wide text-ink-muted">
          sections
        </span>
        <div className="space-y-3">
          {profile.sections.map((section, i) => (
            <div key={i} className="space-y-1 border border-rule p-2">
              <input
                value={section.title}
                onChange={(e) => {
                  const sections = [...profile.sections];
                  sections[i] = { ...sections[i], title: e.target.value };
                  setProfile({ ...profile, sections });
                }}
                placeholder="section title"
                className="w-full bg-transparent font-mono text-xs text-ink outline-none"
              />
              <textarea
                value={section.content}
                onChange={(e) => {
                  const sections = [...profile.sections];
                  sections[i] = { ...sections[i], content: e.target.value };
                  setProfile({ ...profile, sections });
                }}
                rows={3}
                className="w-full resize-y bg-transparent font-serif text-sm text-ink outline-none"
              />
              <button
                type="button"
                onClick={() =>
                  setProfile({
                    ...profile,
                    sections: profile.sections.filter((_, idx) => idx !== i),
                  })
                }
                className="font-mono text-[11px] text-signal hover:underline"
              >
                remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() =>
              setProfile({ ...profile, sections: [...profile.sections, { title: "", content: "" }] })
            }
            className="font-mono text-[11px] text-ink-muted hover:text-phosphor"
          >
            + add section
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="font-mono text-xs text-ink-muted transition-colors hover:text-phosphor disabled:opacity-40"
        >
          {saving ? "saving…" : "[save]"}
        </button>
        <button
          type="button"
          onClick={reindex}
          disabled={reindexing}
          className="font-mono text-xs text-ink-muted transition-colors hover:text-phosphor disabled:opacity-40"
        >
          {reindexing ? "reindexing…" : "[rebuild rag index]"}
        </button>
        {status && <span className="font-mono text-xs text-phosphor">{status}</span>}
        {error && <span className="font-mono text-xs text-signal">{error}</span>}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block font-mono text-[11px] uppercase tracking-wide text-ink-muted">
        {label}
      </span>
      {children}
    </label>
  );
}
