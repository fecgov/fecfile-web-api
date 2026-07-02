import boto3
from fecfiler.settings import SES_ACCESS_KEY_ID, SES_SECRET_ACCESS_KEY, SES_REGION

if SES_ACCESS_KEY_ID and SES_SECRET_ACCESS_KEY and SES_REGION:
    session = boto3.session.Session()
    SES_CLIENT = session.client(
        "sesv2",
        aws_access_key_id=SES_ACCESS_KEY_ID,
        aws_secret_access_key=SES_SECRET_ACCESS_KEY,
        region_name=SES_REGION,
    )
else:
    SES_CLIENT = None


def send_email_notification(from_email, to_email, subject, body_text):
    if SES_CLIENT is None:
        raise RuntimeError(
            "SES client is not configured. Ensure SES_ACCESS_KEY_ID, "
            "SES_SECRET_ACCESS_KEY, and SES_REGION are set."
        )

    return SES_CLIENT.send_email(
        FromEmailAddress=from_email,
        Destination={"ToAddresses": [to_email]},
        Content={
            "Simple": {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}},
            }
        },
    )
