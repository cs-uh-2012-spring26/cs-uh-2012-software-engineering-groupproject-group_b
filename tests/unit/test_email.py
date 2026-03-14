"""
Unit tests for the email reminder service (app/email.py).

Tests the send_class_reminder() function directly, with:
  - boto3.client patched so no real AWS SES calls are made
  - Environment variables patched so no real credentials are needed

This ensures the email formatting and error-handling logic is covered
without any external network calls or AWS account requirements.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from app.email import send_class_reminder


# ─── Shared fixture ───────────────────────────────────────────────────────────


# Fake AWS environment variables — no real credentials needed in tests
_FAKE_ENV = {
    "SES_SENDER_EMAIL":      "sender@example.com",
    "AWS_SES_REGION":        "us-east-1",
    "AWS_ACCESS_KEY_ID":     "FAKEKEYID",
    "AWS_SECRET_ACCESS_KEY": "FAKESECRETKEY",
}

# A minimal class_info dict that mirrors what the DB returns
_CLASS_INFO = {
    "name":         "Morning Yoga",
    "description":  "Gentle yoga for all levels",
    "trainer_name": "Trainer Jane",
    "start_time":   datetime.now() + timedelta(hours=2),
    "end_time":     datetime.now() + timedelta(hours=3),
    "room_number":  "101",
}


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_send_reminder_success():
    """
    When SES accepts the email, send_class_reminder returns (True, "").
    boto3.client is mocked so no real AWS call is made.
    """
    with patch.dict(os.environ, _FAKE_ENV):
        mock_ses = MagicMock()
        with patch("app.email.boto3.client", return_value=mock_ses):
            ok, err = send_class_reminder(
                member_email="member@example.com",
                member_name="Alice",
                class_info=_CLASS_INFO,
            )

    assert ok is True
    assert err == ""
    # Verify SES send_email was called with the correct source address
    mock_ses.send_email.assert_called_once()
    call_kwargs = mock_ses.send_email.call_args[1]
    assert call_kwargs["Source"] == "sender@example.com"
    assert call_kwargs["Destination"]["ToAddresses"] == ["member@example.com"]


def test_send_reminder_ses_client_error():
    """
    When SES raises a ClientError, send_class_reminder returns (False, error_message).
    This exercises the except ClientError branch in email.py.
    """
    with patch.dict(os.environ, _FAKE_ENV):
        mock_ses = MagicMock()
        # Simulate SES rejecting the email (e.g. unverified address in sandbox mode)
        mock_ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "Email address not verified"}},
            "SendEmail",
        )
        with patch("app.email.boto3.client", return_value=mock_ses):
            ok, err = send_class_reminder(
                member_email="unverified@example.com",
                member_name="Bob",
                class_info=_CLASS_INFO,
            )

    assert ok is False
    assert "not verified" in err


def test_send_reminder_with_string_datetimes():
    """
    If start_time or end_time are plain strings (not datetime objects),
    the function falls back to str() formatting instead of strftime().
    This exercises the else branches in the date formatting code.
    """
    class_info_strings = {
        "name":         "String Time Class",
        "description":  "desc",
        "trainer_name": "Trainer",
        "start_time":   "2026-05-01 10:00:00",   # plain string, not datetime
        "end_time":     "2026-05-01 11:00:00",   # plain string, not datetime
        "room_number":  "202",
    }
    with patch.dict(os.environ, _FAKE_ENV):
        mock_ses = MagicMock()
        with patch("app.email.boto3.client", return_value=mock_ses):
            ok, err = send_class_reminder(
                member_email="member@example.com",
                member_name="Carol",
                class_info=class_info_strings,
            )

    # Should still succeed — string fallback path runs without error
    assert ok is True
    assert err == ""


def test_send_reminder_missing_env_variable():
    """
    If a required AWS environment variable is missing, _get_env raises
    EnvironmentError and the function propagates it.
    This exercises the _get_env validation branch.
    """
    # Provide all vars except the sender email — should raise EnvironmentError
    incomplete_env = {k: v for k, v in _FAKE_ENV.items() if k != "SES_SENDER_EMAIL"}

    # Remove SES_SENDER_EMAIL from the environment entirely for this test
    env_without_sender = {**incomplete_env, "SES_SENDER_EMAIL": ""}

    with patch.dict(os.environ, env_without_sender, clear=False):
        # Also remove it from os.environ directly in case .env file sets it
        os.environ.pop("SES_SENDER_EMAIL", None)
        with pytest.raises(EnvironmentError):
            send_class_reminder(
                member_email="member@example.com",
                member_name="Dave",
                class_info=_CLASS_INFO,
            )
