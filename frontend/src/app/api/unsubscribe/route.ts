import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function POST(req: NextRequest) {
  const { token } = await req.json().catch(() => ({}));

  if (!token || typeof token !== "string") {
    return NextResponse.json({ error: "Missing token" }, { status: 400 });
  }

  const { data, error } = await supabase
    .from("subscriptions")
    .update({ is_active: false })
    .eq("unsubscribe_token", token)
    .eq("is_active", true)
    .select("id");

  if (error || !data || data.length === 0) {
    return NextResponse.json({ error: "Token not found or already used" }, { status: 404 });
  }

  return NextResponse.json({ ok: true });
}
