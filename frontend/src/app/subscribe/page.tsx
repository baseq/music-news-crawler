"use client";
import { useEffect, useState } from "react";
import { supabase, Channel } from "@/lib/supabase";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "ro", label: "Română" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "it", label: "Italiano" },
  { code: "es", label: "Español" },
];

function SubscribeForm() {
  const searchParams = useSearchParams();
  const preselectedSlug = searchParams.get("channel");

  const [channels, setChannels]       = useState<Channel[]>([]);
  const [email, setEmail]             = useState("");
  const [language, setLanguage]       = useState("en");
  const [selected, setSelected]       = useState<Set<string>>(new Set());
  const [loading, setLoading]         = useState(false);
  const [submitted, setSubmitted]     = useState(false);
  const [error, setError]             = useState("");

  useEffect(() => {
    supabase
      .from("channels")
      .select("*")
      .eq("is_active", true)
      .order("sort_order")
      .then(({ data }) => {
        setChannels(data ?? []);
        if (preselectedSlug) {
          const match = (data ?? []).find((c: Channel) => c.slug === preselectedSlug);
          if (match) setSelected(new Set([match.id]));
        }
      });
  }, [preselectedSlug]);

  function toggleChannel(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!email.trim()) { setError("Please enter your email."); return; }
    if (selected.size === 0) { setError("Please select at least one channel."); return; }

    setLoading(true);
    const res = await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        channel_ids: [...selected],
        preferred_language: language,
      }),
    });
    setLoading(false);

    if (res.ok) {
      setSubmitted(true);
    } else {
      const body = await res.json().catch(() => ({}));
      setError(body.error ?? "Something went wrong. Please try again.");
    }
  }

  if (submitted) {
    return (
      <div className="max-w-lg mx-auto text-center py-20">
        <div className="text-5xl mb-6">🎉</div>
        <h1 className="text-3xl font-bold text-heading mb-4">You're in!</h1>
        <p className="text-subtle leading-relaxed">
          Your first digest will arrive tomorrow morning (6am UTC) for each
          channel you subscribed to. Check your spam folder if you don't see it.
        </p>
        <a href="/channels" className="mt-8 inline-block text-accent-light hover:underline text-sm">
          Browse channels →
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-heading mb-3">Subscribe</h1>
        <p className="text-subtle">
          No account needed. Pick your channels and language, enter your email — done.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-heading mb-2">
            Email address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-3 bg-surface border border-border rounded-lg text-heading placeholder-muted focus:outline-none focus:border-accent-light transition-colors"
            required
          />
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-heading mb-2">
            Digest language
          </label>
          <p className="text-xs text-muted mb-3">
            Summaries will be translated into this language. Original articles always link to their source.
          </p>
          <div className="flex flex-wrap gap-2">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => setLanguage(l.code)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  language === l.code
                    ? "bg-accent text-white"
                    : "border border-border text-subtle hover:border-heading hover:text-heading"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Channels */}
        <div>
          <label className="block text-sm font-medium text-heading mb-2">
            Channels{" "}
            <span className="text-muted font-normal">
              ({selected.size} selected)
            </span>
          </label>
          <div className="grid grid-cols-1 gap-2">
            {channels.map((ch) => {
              const checked = selected.has(ch.id);
              return (
                <button
                  key={ch.id}
                  type="button"
                  onClick={() => toggleChannel(ch.id)}
                  className={`flex items-center gap-4 p-4 rounded-xl border text-left transition-all ${
                    checked
                      ? "border-accent-light bg-accent/10 text-heading"
                      : "border-border bg-surface text-subtle hover:border-heading"
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded flex items-center justify-center shrink-0 border transition-colors ${
                      checked ? "bg-accent border-accent" : "border-border"
                    }`}
                  >
                    {checked && (
                      <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </div>
                  <span className="text-xl">{ch.icon}</span>
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-heading">{ch.name}</p>
                    <p className="text-xs text-muted truncate">{ch.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-900/20 border border-red-900/40 rounded-lg px-4 py-3">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 bg-accent text-white rounded-full font-semibold text-base hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Subscribing..." : "Subscribe →"}
        </button>

        <p className="text-xs text-muted text-center">
          Every email includes a one-click unsubscribe link.
        </p>
      </form>
    </div>
  );
}

export default function SubscribePage() {
  return (
    <Suspense fallback={<div className="text-subtle">Loading...</div>}>
      <SubscribeForm />
    </Suspense>
  );
}
