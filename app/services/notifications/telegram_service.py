import json
import urllib.error
import urllib.request

from app.config import Config
from app.services.notifications.base import NotificationService


class TelegramNotificationService(NotificationService):

    def send(self, member: dict, class_info: dict) -> tuple[bool, str]:
        chat_id = member.get("telegram_chat_id")
        if not chat_id:
            return False, "Member has no telegram_chat_id"

        msg  = self._build_message(member.get("name", ""), class_info)
        url  = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": msg["body"]}).encode()
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
                return True, ""
        except urllib.error.HTTPError as e:
            return False, f"Telegram error {e.code}: {e.reason}"
        except Exception as e:
            return False, f"Telegram error: {e}"
