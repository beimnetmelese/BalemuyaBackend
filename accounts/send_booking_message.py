import os
import requests

BOT_SERVER_URL = os.getenv("BOT_SERVER_URL", "https://balemuyabot.onrender.com")


def send_booking_message_sync(telegram_id, message, button_text, button_url):
    """
    Send a booking message via the FastAPI bot service.
    """
    payload = {
        "telegram_id": str(telegram_id),
        "message": message,
        "button_text": button_text,
        "button_url": button_url,
    }
    try:
        requests.post(
            f"{BOT_SERVER_URL}/telegram/send",
            json=payload,
            timeout=10,
        )
    except Exception:
        # Best-effort fire-and-forget; avoid breaking booking flow.
        pass
