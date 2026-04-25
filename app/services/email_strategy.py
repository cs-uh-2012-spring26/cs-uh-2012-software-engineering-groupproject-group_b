import boto3
from botocore.exceptions import ClientError
from os import environ
# from dotenv import load_dotenv
from typing import Dict, Tuple
from datetime import datetime

from app.services.notification_strategy import NotificationStrategy


class Emailstrategy(NotificationStrategy):
    """ Email notification strategy using AWS SES."""

    def __init__(self):
        """ Initialize AWS SES client """
        self.sender = self._get_env("SES_SENDER_EMAIL")
        self.region = self._get_env("AWS_SES_REGION")
        key_id = self._get_env("AWS_ACCESS_KEY_ID")
        secret_key = self._get_env("AWS_SECRET_ACCESS_KEY")

        self.ses_client = boto3.client(
            "ses",
            region_name=self.region,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret_key,
        )

    def send_reminder(self, recipient: str, name: str, class_info: Dict) -> Tuple[bool, str]:
        """ Send reminder email via AWS SES """
        subject = self._format_subject(class_info)
        body = self._format_body(name, class_info)

        try:
            self.ses_client.send_email(
                Source=self.sender,
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )
            return True, ""
        except ClientError as e:
            return False, e.response["Error"]["Message"]

    """ Private header methods defined"""

    def format_subject(self, class_info: Dict) -> str:
        """ Email subject line """
        class_name = class_info.get("name", "")
        return f"Reminder: Upcoming class - {class_name}"

    def format_body(self, member_name: str, class_info: Dict) -> str:
        """ Format email body with all class details """
        date_str, start_str, end_str = self._format_dates(class_info)

        return (
            f"Dear {member_name},\n\n"
            f"This is a reminder for your upcoming fitness class:\n\n"
            f"  Class:       {class_info.get('name', '')}\n"
            f"  Description: {class_info.get('description', '')}\n"
            f"  Trainer:     {class_info.get('trainer_name', '')}\n"
            f"  Date:        {date_str}\n"
            f"  Time:        {start_str} - {end_str}\n"
            f"  Room:        {class_info.get('room_number', '')}\n\n"
            f"We look forward to seeing you!\n"
        )

    def format_dates(self, class_info: Dict) -> Tuple[str, str, str]:
        """ Format dates and time strings form class info """
        start_dt = class_info.get("start_time")
        end_dt = class_info.get("end_time")

        if hasattr(start_dt, "strftime"):
            date_str = start_dt.strftime("%A, %B %d, %Y")
            start_str = start_dt.strftime("%I:%M %p")
        else:
            date_str = str(start_dt)
            start_str = str(start_dt)

        end_str = end_dt.strftime("%I:%M %p") if hasattr(
            end_dt, "strftime") else str(end_dt)

        return date_str, start_str, end_str

    @staticmethod
    def _get_env(name: str) -> str:
        """ Get required environment variable """
        value = environ.get(name, "")
        if not value.strip():
            raise EnvironmentError(
                f"Required environment variable {name} is not set")
        return value
