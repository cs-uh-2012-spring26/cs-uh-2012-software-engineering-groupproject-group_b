from app.services.notifications.email_service    import EmailNotificationService
from app.services.notifications.telegram_service import TelegramNotificationService

_DEFAULT_PREFS: dict[str, bool] = {"email": True, "telegram": False}

_SERVICE_REGISTRY: dict[str, type] = {
    "email":    EmailNotificationService,
    "telegram": TelegramNotificationService,
}


class NotificationDispatcher:

    def dispatch_to_member(
        self, member: dict, class_info: dict
    ) -> tuple[bool, list[str]]:
        """Send reminders on ALL channels the member has enabled."""
        prefs  = member.get("notification_prefs") or _DEFAULT_PREFS
        errors: list[str] = []
        for channel, service_cls in _SERVICE_REGISTRY.items():
            if not prefs.get(channel, False):
                continue
            ok, err = service_cls().send(member, class_info)
            if not ok:
                errors.append(f"[{channel}] {err}")
        return len(errors) == 0, errors
