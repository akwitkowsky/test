import os
import json
import base64
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import anthropic
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]
DRIVE_FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

CLASSIFY_PROMPT = """Classify this screenshot for personal knowledge management.
Respond with ONLY valid JSON, no markdown, no extra text.

{
  "category": "business" | "delete" | "unclear",
  "title": "brief 3-6 word title",
  "source_url": "url if clearly visible in screenshot, else null",
  "key_insights": ["insight 1", "insight 2", "insight 3"]
}

Rules:
- business: tech, AI, research, code, professional tools, articles worth referencing later
- delete: memes, entertainment, social posts with no reference value, random photos
- unclear: genuinely ambiguous — use sparingly, only when you truly cannot decide

key_insights: 2-3 specific takeaways. Empty array [] if category is delete."""


def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        "service_account.json", scopes=DRIVE_SCOPES
    )
    return build("drive", "v3", credentials=creds)


def save_to_drive(image_b64: str, result: dict, timestamp: str) -> str:
    service = get_drive_service()
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else datetime.now(timezone.utc)
    safe_title = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in result.get("title", "screenshot").lower()
    )[:50]
    base_name = f"{dt.strftime('%Y%m%d_%H%M%S')}_{safe_title}"

    image_bytes = base64.b64decode(image_b64)
    img_media = MediaInMemoryUpload(image_bytes, mimetype="image/png", resumable=False)
    service.files().create(
        body={"name": f"{base_name}.png", "parents": [DRIVE_FOLDER_ID]},
        media_body=img_media,
    ).execute()

    insights = result.get("key_insights") or []
    md = f"# {result.get('title', 'Screenshot')}\n\n"
    md += f"**Captured:** {dt.strftime('%Y-%m-%d %H:%M UTC')}\n"
    md += f"**Source:** {result.get('source_url') or 'N/A'}\n\n"
    md += "## Key Insights\n\n"
    md += "".join(f"- {i}\n" for i in insights) if insights else "_No insights extracted._\n"

    md_media = MediaInMemoryUpload(md.encode(), mimetype="text/markdown", resumable=False)
    service.files().create(
        body={"name": f"{base_name}.md", "parents": [DRIVE_FOLDER_ID]},
        media_body=md_media,
    ).execute()

    return base_name


def send_slack(text: str):
    requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=10)


@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET and request.headers.get("X-Secret") != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    image_b64 = data.get("image_data", "")
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

    if not image_b64:
        return jsonify({"error": "no image_data"}), 400

    msg = claude.messages.create(
        model="claude-opus-4-7",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": CLASSIFY_PROMPT},
            ],
        }],
    )

    result = json.loads(msg.content[0].text)
    category = result.get("category", "unclear")

    if category == "business":
        name = save_to_drive(image_b64, result, timestamp)
        send_slack(f"📁 Filed: *{result.get('title', name)}*")
        return jsonify({"action": "saved", "title": result.get("title", "")})

    if category == "delete":
        return jsonify({"action": "delete"})

    # unclear — ping Slack for a human decision
    send_slack(
        f"📸 *Screenshot needs a call*\n"
        f"Claude: couldn't classify confidently\n\n"
        f"Options:\n"
        f"• `keep` — file it to Drive\n"
        f"• `delete` — purge it\n"
        f"• `skip` — ignore\n\n"
        f"_(captured {timestamp})_"
    )
    return jsonify({"action": "unclear"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
