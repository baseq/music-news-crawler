import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { Resend } from "resend";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!   // service key — used only server-side
);

const resend = new Resend(process.env.RESEND_API_KEY);
const FROM_EMAIL = process.env.RESEND_FROM_EMAIL ?? "digest@musicdigest.app";
const FROM_NAME  = process.env.RESEND_FROM_NAME  ?? "Music Digest";
const APP_URL    = (process.env.APP_BASE_URL ?? "https://music-digest.org").replace(/\/$/, "");

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function buildWelcomeEmail(
  email: string,
  channelNames: string[],
  preferredLanguage: string,
  unsubscribeUrl: string,
): string {
  const langLabels: Record<string, string> = {
    en: "English", ro: "Română", fr: "Français",
    de: "Deutsch", it: "Italiano", es: "Español",
  };
  const langLabel = langLabels[preferredLanguage] ?? preferredLanguage;

  const channelList = channelNames
    .map((n) => `<li style="margin: 4px 0; color: #c7d2fe;">${n}</li>`)
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Welcome to Music Digest</title></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#13131a;border:1px solid #1e1e2e;border-radius:12px;max-width:600px;width:100%;">

        <!-- Header -->
        <tr><td style="padding:40px 40px 24px;border-bottom:1px solid #1e1e2e;">
          <p style="margin:0;font-size:28px;font-weight:700;color:#e2e8f0;">🎵 Music Digest</p>
          <p style="margin:8px 0 0;font-size:14px;color:#6b7280;">Your curated music news, delivered daily</p>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:32px 40px;">
          <h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#e2e8f0;">Welcome aboard! 🎉</h1>
          <p style="margin:0 0 20px;font-size:15px;color:#94a3b8;line-height:1.6;">
            You're now subscribed to daily music news digests. We'll send you a curated summary every morning at <strong style="color:#e2e8f0;">6 am UTC</strong>.
          </p>

          <p style="margin:0 0 10px;font-size:14px;font-weight:600;color:#a5b4fc;text-transform:uppercase;letter-spacing:0.05em;">Your channels</p>
          <ul style="margin:0 0 20px;padding:0 0 0 20px;">
            ${channelList}
          </ul>

          <p style="margin:0 0 20px;font-size:15px;color:#94a3b8;line-height:1.6;">
            Summaries will be delivered in <strong style="color:#e2e8f0;">${langLabel}</strong>.
            You can change your language preference anytime by re-subscribing with a different language.
          </p>

          <table cellpadding="0" cellspacing="0" style="margin:24px 0;">
            <tr><td style="background:#4f46e5;border-radius:8px;">
              <a href="${APP_URL}/channels" style="display:inline-block;padding:12px 28px;font-size:14px;font-weight:600;color:#fff;text-decoration:none;">
                Browse channels →
              </a>
            </td></tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:20px 40px;border-top:1px solid #1e1e2e;">
          <p style="margin:0;font-size:12px;color:#4b5563;line-height:1.6;">
            You're receiving this because you subscribed at ${APP_URL}.<br>
            <a href="${unsubscribeUrl}" style="color:#6366f1;text-decoration:none;">Unsubscribe</a> from all future emails.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
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

  // Check if this email already has active subscriptions (to detect first-time vs re-subscribe)
  const { data: existing } = await supabase
    .from("subscriptions")
    .select("id")
    .eq("email", email)
    .eq("is_active", true)
    .limit(1);

  const isFirstSubscription = !existing || existing.length === 0;

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

  // Send welcome email only on first subscription
  if (isFirstSubscription && process.env.RESEND_API_KEY) {
    try {
      // Fetch channel names
      const { data: channels } = await supabase
        .from("channels")
        .select("name, slug")
        .in("id", channel_ids);

      const channelNames = (channels ?? []).map((c: { name: string; slug: string }) => c.name);

      // Build an unsubscribe URL using the first channel's slug as a placeholder
      // Real per-email unsubscribe tokens are handled by the newsletter sender
      const unsubscribeUrl = `${APP_URL}/unsubscribe`;

      const html = buildWelcomeEmail(email, channelNames, preferred_language, unsubscribeUrl);

      await resend.emails.send({
        from: `${FROM_NAME} <${FROM_EMAIL}>`,
        to: email,
        subject: `Welcome to Music Digest 🎵`,
        html,
        headers: {
          "List-Unsubscribe": `<${unsubscribeUrl}>`,
        },
      });
    } catch (emailErr) {
      // Non-fatal — subscription already saved, just log the email failure
      console.error("Welcome email failed:", emailErr);
    }
  }

  return NextResponse.json({ ok: true });
}
