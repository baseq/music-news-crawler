"""
Newsletter sender — sends email payloads via Resend.

Entry point for the daily newsletter job.
Run: python newsletter/sender.py
"""
import logging
import os
import time
import sys
from datetime import date, datetime, timezone

from dotenv import load_dotenv
import resend
from supabase import create_client

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from newsletter.builder import build_emails, EmailPayload

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("newsletter.sender")

resend.api_key = os.environ["RESEND_API_KEY"]
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "digest@yourdomain.com")
FROM_NAME  = os.environ.get("RESEND_FROM_NAME", "Music Digest")
DRY_RUN    = os.environ.get("DRY_RUN", "false").lower() == "true"

BATCH_SIZE       = 10   # emails per batch
BATCH_DELAY_SECS = 1.5  # pause between batches (rate limit safety)


def send_email(payload: EmailPayload) -> bool:
    """Send a single email via Resend. Returns True on success."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would send to {payload.to_email}: {payload.subject}")
        return True

    try:
        resend.Emails.send({
            "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
            "to":      [payload.to_email],
            "subject": payload.subject,
            "html":    payload.html,
            "headers": {
                "List-Unsubscribe": f"<{os.environ.get('APP_BASE_URL','')}/unsubscribe?token={payload.unsubscribe_token}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        })
        return True
    except Exception as e:
        logger.error(f"  Send failed to {payload.to_email}: {e}")
        return False


def update_subscriber_sent_at(supabase, subscription_id: str):
    try:
        supabase.table("subscriptions").update({
            "last_sent_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", subscription_id).execute()
    except Exception:
        pass


def update_issue_sent(supabase, channel_id: str, recipient_count: int):
    try:
        supabase.table("newsletter_issues").update({
            "sent_at":        datetime.now(timezone.utc).isoformat(),
            "recipient_count": recipient_count,
        }).eq("channel_id", channel_id).eq("issue_date", date.today().isoformat()).execute()
    except Exception:
        pass


def main():
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    logger.info("Building email payloads...")
    payloads = build_emails(supabase)
    logger.info(f"Total emails to send: {len(payloads)}")

    if not payloads:
        logger.info("Nothing to send today.")
        return

    sent = 0
    failed = 0
    channel_counts: dict[str, int] = {}

    # Send in batches
    for i in range(0, len(payloads), BATCH_SIZE):
        batch = payloads[i : i + BATCH_SIZE]
        for payload in batch:
            ok = send_email(payload)
            if ok:
                sent += 1
                channel_counts[payload.channel_id] = channel_counts.get(payload.channel_id, 0) + 1
                update_subscriber_sent_at(supabase, payload.subscription_id)
            else:
                failed += 1

        if i + BATCH_SIZE < len(payloads):
            time.sleep(BATCH_DELAY_SECS)

    # Update issue records with recipient counts
    for channel_id, count in channel_counts.items():
        update_issue_sent(supabase, channel_id, count)

    logger.info(
        f"\n{'─'*50}\n"
        f"  Newsletter complete\n"
        f"  Sent:    {sent}\n"
        f"  Failed:  {failed}\n"
        f"{'─'*50}"
    )


if __name__ == "__main__":
    main()
