"""Instagram Graph API bilan ishlash — xabar va izoh yuborish."""
import requests

import config


def send_dm(recipient_id: str, text: str) -> bool:
    """Foydalanuvchiga to'g'ridan-to'g'ri xabar (DM) yuboradi."""
    # Instagram Login API'da "me" ishlatiladi (o'z akkauntimiz nomidan)
    url = f"{config.GRAPH_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    params = {"access_token": config.IG_ACCESS_TOKEN}
    try:
        r = requests.post(url, json=payload, params=params, timeout=15)
        if r.status_code >= 400:
            print(f"[IG DM xato] {r.status_code}: {r.text}")
            return False
        print(f"[IG DM yuborildi] -> {recipient_id}")
        return True
    except Exception as e:
        print(f"[IG DM istisno] {e}")
        return False


def reply_to_comment(comment_id: str, text: str) -> bool:
    """Post izohiga commentariya bilan javob yozadi."""
    url = f"{config.GRAPH_URL}/{comment_id}/replies"
    payload = {"message": text}
    params = {"access_token": config.IG_ACCESS_TOKEN}
    try:
        r = requests.post(url, data=payload, params=params, timeout=15)
        if r.status_code >= 400:
            print(f"[IG izoh xato] {r.status_code}: {r.text}")
            return False
        print(f"[IG izohga javob yozildi] -> {comment_id}")
        return True
    except Exception as e:
        print(f"[IG izoh istisno] {e}")
        return False
