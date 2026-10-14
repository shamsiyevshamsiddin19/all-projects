"""
Instagram aqlli bot — webhook server.

Ishga tushirish:
    python app.py

Bot quyidagilarga avtomatik javob beradi:
  - DM (to'g'ridan-to'g'ri xabarlar)
  - Story mention (story'da belgilash) -> DM orqali
  - Post izohlari (comments)
"""
from flask import Flask, request

import config
import gemini_client
import instagram_client

app = Flask(__name__)

# Bir xil xabarga ikki marta javob bermaslik uchun (Meta ba'zan takroran yuboradi)
_seen_ids = set()


def _once(event_id: str) -> bool:
    """True qaytarsa — bu hodisa yangi (birinchi marta)."""
    if not event_id or event_id in _seen_ids:
        return False
    _seen_ids.add(event_id)
    # xotira to'lib ketmasin
    if len(_seen_ids) > 5000:
        _seen_ids.clear()
    return True


@app.get("/webhook")
def verify():
    """Meta webhook'ni ulaganda bir marta tekshiradi."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        print("[Webhook tasdiqlandi]")
        return challenge, 200
    return "Tekshiruv muvaffaqiyatsiz", 403


@app.post("/webhook")
def receive():
    """Instagram'dan kelgan hodisalarni qabul qiladi."""
    data = request.get_json(silent=True) or {}

    for entry in data.get("entry", []):
        # 1) Xabarlar (DM va story mention)
        for msg in entry.get("messaging", []):
            _handle_message(msg)

        # 2) Izohlar va boshqa o'zgarishlar
        for change in entry.get("changes", []):
            if change.get("field") == "comments":
                _handle_comment(change.get("value", {}))

    # Meta'ga har doim 200 qaytarish shart
    return "OK", 200


def _handle_message(msg: dict):
    """DM yoki story mention'ga javob beradi."""
    sender_id = msg.get("sender", {}).get("id")
    message = msg.get("message", {})
    mid = message.get("mid")

    # O'z xabarimizga (echo) javob bermaymiz
    if message.get("is_echo"):
        return
    if not sender_id or not _once(mid):
        return

    text = message.get("text", "")
    attachments = message.get("attachments", [])

    # Story mention aniqlash
    is_story_mention = any(
        a.get("type") == "story_mention" for a in attachments
    )

    if is_story_mention:
        reply = gemini_client.generate_reply(
            "Foydalanuvchi meni o'z story'sida belgiladi.",
            context="Bu odam seni story'da belgiladi. Unga samimiy rahmat ayt.",
        )
    elif text:
        reply = gemini_client.generate_reply(text, context="Bu to'g'ridan-to'g'ri xabar (DM).")
    else:
        # Matnsiz xabar (rasm/stiker) — oddiy javob
        reply = "Xabaringiz uchun rahmat! 🙌"

    instagram_client.send_dm(sender_id, reply)


def _handle_comment(value: dict):
    """Post izohiga javob beradi."""
    comment_id = value.get("id")
    text = value.get("text", "")
    from_user = value.get("from", {}).get("id")

    # O'zimizning izohimizga javob bermaymiz
    if from_user and from_user == config.IG_ACCOUNT_ID:
        return
    if not comment_id or not _once(comment_id) or not text:
        return

    reply = gemini_client.generate_reply(
        text, context="Bu sizning postingizga yozilgan izoh. Qisqa va samimiy javob ber."
    )
    instagram_client.reply_to_comment(comment_id, reply)


@app.get("/")
def home():
    return "Instagram bot ishlayapti ✅", 200


if __name__ == "__main__":
    config.check()
    print("Bot ishga tushdi -> http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
