import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!   // service key — used only server-side
);

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export async function POST(req: NextRequest) {
  let body: { email?: string; channel_ids?: string[]; preferred_language?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { email, channel_ids, preferred_language = "en" } = body;

  if (!email || !isValidEmail(email)) {
    return NextResponse.json({ error: "Invalid email address" }, { status: 400 });
  }
  if (!channel_ids || channel_ids.length === 0) {
    return NextResponse.json({ error: "Select at least one channel" }, { status: 400 });
  }

  const VALID_LANGS = ["en", "ro", "fr", "de", "it", "es"];
  if (!VALID_LANGS.includes(preferred_language)) {
    return NextResponse.json({ error: "Invalid language" }, { status: 400 });
  }

  // Upsert a subscription row per channel
  const rows = channel_ids.map((channel_id) => ({
    email,
    channel_id,
    preferred_language,
    is_active: true,
  }));

  const { error } = await supabase
    .from("subscriptions")
    .upsert(rows, { onConflict: "email,channel_id", ignoreDuplicates: false });

  if (error) {
    console.error("Subscribe error:", error);
    return NextResponse.json({ error: "Subscription failed. Please try again." }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
