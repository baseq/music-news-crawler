"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

function UnsubscribeContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error" | "missing">("loading");

  useEffect(() => {
    if (!token) { setStatus("missing"); return; }

    fetch("/api/unsubscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((r) => setStatus(r.ok ? "success" : "error"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <div className="max-w-md mx-auto text-center py-24">
      {status === "loading" && (
        <>
          <div className="text-4xl mb-4 animate-pulse">⏳</div>
          <p className="text-subtle">Unsubscribing...</p>
        </>
      )}
      {status === "success" && (
        <>
          <div className="text-5xl mb-6">👋</div>
          <h1 className="text-3xl font-bold text-heading mb-4">Unsubscribed</h1>
          <p className="text-subtle leading-relaxed">
            You've been removed. No more emails from this channel.
          </p>
          <a href="/channels" className="mt-8 inline-block text-accent-light hover:underline text-sm">
            Browse other channels →
          </a>
        </>
      )}
      {status === "error" && (
        <>
          <div className="text-5xl mb-6">❌</div>
          <h1 className="text-3xl font-bold text-heading mb-4">Something went wrong</h1>
          <p className="text-subtle">This unsubscribe link may have already been used or is invalid.</p>
        </>
      )}
      {status === "missing" && (
        <>
          <div className="text-5xl mb-6">🔗</div>
          <h1 className="text-3xl font-bold text-heading mb-4">Invalid link</h1>
          <p className="text-subtle">No token found. Use the unsubscribe link from your email.</p>
        </>
      )}
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={<div className="text-subtle text-center py-24">Loading...</div>}>
      <UnsubscribeContent />
    </Suspense>
  );
}
