import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from os import environ


def _get_env(name: str) -> str:
    load_dotenv(override=True)
    value = environ.get(name, "")
    if not value.strip():
        raise EnvironmentError(f"Required environment variable {name} is not set")
    return value


def send_class_reminder(
    member_email: str,
    member_name: str,
    class_info: dict,
) -> tuple[bool, str]:
    """
    Send a class reminder email to a single member via Amazon SES.

    Args:
        member_email: Recipient's email address (must be SES-verified in sandbox mode).
        member_name:  Recipient's display name.
        class_info:   Serialized class document from the database.

    Returns:
        (True, "")              – email sent successfully
        (False, error_message)  – SES rejected or failed to deliver
    """
    sender = _get_env("SES_SENDER_EMAIL")
    region = _get_env("AWS_SES_REGION")
    key_id = _get_env("AWS_ACCESS_KEY_ID")
    secret_key = _get_env("AWS_SECRET_ACCESS_KEY")

    ses_client = boto3.client(
        "ses",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret_key,
    )

    start_dt = class_info.get("start_time")
    end_dt = class_info.get("end_time")

    if hasattr(start_dt, "strftime"):
        date_str = start_dt.strftime("%A, %B %d, %Y")
        start_str = start_dt.strftime("%I:%M %p")
    else:
        date_str = str(start_dt)
        start_str = str(start_dt)

    end_str = end_dt.strftime("%I:%M %p") if hasattr(end_dt, "strftime") else str(end_dt)

    class_name = class_info.get("name", "")
    subject = f"Reminder: Upcoming Class – {class_name}"

    body = (
        f"Dear {member_name},\n\n"
        f"This is a reminder for your upcoming fitness class:\n\n"
        f"  Class:       {class_name}\n"
        f"  Description: {class_info.get('description', '')}\n"
        f"  Trainer:     {class_info.get('trainer_name', '')}\n"
        f"  Date:        {date_str}\n"
        f"  Time:        {start_str} \u2013 {end_str}\n"
        f"  Room:        {class_info.get('room_number', '')}\n\n"
        f"We look forward to seeing you!\n"
    )

    try:
        ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [member_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        return True, ""
    except ClientError as e:
        return False, e.response["Error"]["Message"]
