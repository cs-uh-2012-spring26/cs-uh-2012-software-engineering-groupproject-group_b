"""
Unit tests for notification service classes.

Services covered:
  NotificationService._build_message        — builds subject and body from class info
  EmailNotificationService.send             — sends reminder via AWS SES
  TelegramNotificationService.send          — sends reminder via Telegram Bot API
  NotificationDispatcher.dispatch_to_member — routes reminder to enabled channels
"""

import urllib.error
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from app.services.notifications.email_service import EmailNotificationService
from app.services.notifications.telegram_service import TelegramNotificationService
from app.services.notifications.dispatcher import NotificationDispatcher


_CLASS = {
    "name": "Yoga",
    "description": "Relaxing session",
    "trainer_name": "Sam",
    "date": "2030-01-01",
    "start_time": "10:00",
    "end_time": "11:00",
    "room_number": "101",
}
_MEMBER    = {"name": "Alice", "email": "alice@example.com"}
_MEMBER_TG = {**_MEMBER, "telegram_chat_id": "123456"}


# ─── Tests: _build_message ────────────────────────────────────────────────────


def test_build_message_subject():
    """Subject contains the class name."""
    msg = EmailNotificationService()._build_message("Alice", _CLASS)
    assert "Yoga" in msg["subject"]


def test_build_message_body():
    """Body contains the member name and class start time."""
    msg = EmailNotificationService()._build_message("Alice", _CLASS)
    assert "Alice" in msg["body"]
    assert "10:00" in msg["body"]


# ─── Tests: EmailNotificationService ─────────────────────────────────────────


def test_email_send_success():
    """A successful SES call returns (True, '')."""
    with patch("app.services.notifications.email_service.boto3.client") as mock_boto:
        mock_boto.return_value.send_email.return_value = {}
        ok, err = EmailNotificationService().send(_MEMBER, _CLASS)
    assert ok is True
    assert err == ""


def test_email_send_failure():
    """A ClientError from SES returns (False, error message)."""
    error = {"Error": {"Code": "MessageRejected", "Message": "Address blacklisted"}}
    with patch("app.services.notifications.email_service.boto3.client") as mock_boto:
        mock_boto.return_value.send_email.side_effect = ClientError(error, "SendEmail")
        ok, err = EmailNotificationService().send(_MEMBER, _CLASS)
    assert ok is False
    assert "blacklisted" in err


# ─── Tests: TelegramNotificationService ──────────────────────────────────────


def test_telegram_missing_chat_id():
    """A member without a telegram_chat_id returns (False, error)."""
    ok, err = TelegramNotificationService().send(_MEMBER, _CLASS)
    assert ok is False
    assert "telegram_chat_id" in err


def test_telegram_send_success():
    """A successful Telegram request returns (True, '')."""
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("app.services.notifications.telegram_service.urllib.request.urlopen", return_value=mock_resp):
        ok, err = TelegramNotificationService().send(_MEMBER_TG, _CLASS)
    assert ok is True
    assert err == ""


def test_telegram_http_error():
    """An HTTPError from Telegram returns (False, error with status code)."""
    with patch("app.services.notifications.telegram_service.urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError(None, 400, "Bad Request", {}, None)
        ok, err = TelegramNotificationService().send(_MEMBER_TG, _CLASS)
    assert ok is False
    assert "400" in err


def test_telegram_generic_error():
    """Any unexpected exception returns (False, error message)."""
    with patch("app.services.notifications.telegram_service.urllib.request.urlopen") as mock_open:
        mock_open.side_effect = Exception("timeout")
        ok, err = TelegramNotificationService().send(_MEMBER_TG, _CLASS)
    assert ok is False
    assert "timeout" in err


# ─── Tests: NotificationDispatcher ───────────────────────────────────────────


def test_dispatcher_email_success():
    """A member with email enabled gets a reminder and returns no errors."""
    member = {**_MEMBER, "notification_prefs": {"email": True, "telegram": False}}
    with patch.object(EmailNotificationService, "send", return_value=(True, "")):
        ok, errors = NotificationDispatcher().dispatch_to_member(member, _CLASS)
    assert ok is True
    assert errors == []


def test_dispatcher_no_prefs_defaults_to_email():
    """A member with no notification_prefs falls back to the email default."""
    with patch.object(EmailNotificationService, "send", return_value=(True, "")):
        ok, errors = NotificationDispatcher().dispatch_to_member(_MEMBER, _CLASS)
    assert ok is True


def test_dispatcher_records_failure():
    """A failed channel is recorded in the errors list."""
    member = {**_MEMBER, "notification_prefs": {"email": True}}
    with patch.object(EmailNotificationService, "send", return_value=(False, "SES down")):
        ok, errors = NotificationDispatcher().dispatch_to_member(member, _CLASS)
    assert ok is False
    assert "[email] SES down" in errors
