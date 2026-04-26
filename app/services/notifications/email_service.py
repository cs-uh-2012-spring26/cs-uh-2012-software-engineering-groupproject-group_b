import boto3
from botocore.exceptions import ClientError

from app.config import Config
from app.services.notifications.base import NotificationService


class EmailNotificationService(NotificationService):

    def send(self, member: dict, class_info: dict) -> tuple[bool, str]:
        msg = self._build_message(member.get("name", ""), class_info)
        client = boto3.client(
            "ses",
            region_name=Config.AWS_SES_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        )
        try:
            client.send_email(
                Source=Config.SES_SENDER_EMAIL,
                Destination={"ToAddresses": [member["email"]]},
                Message={
                    "Subject": {"Data": msg["subject"], "Charset": "UTF-8"},
                    "Body":    {"Text": {"Data": msg["body"],    "Charset": "UTF-8"}},
                },
            )
            return True, ""
        except ClientError as e:
            return False, e.response["Error"]["Message"]
