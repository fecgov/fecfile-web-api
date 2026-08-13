from fecfiler.settings import (
    SES_ACCESS_KEY_ID, SES_SECRET_ACCESS_KEY, SES_REGION, SES_DOMAIN, SES_FROM_EMAIL,
    FLAG__ENABLE_EMAIL
)
import boto3
import structlog

logger = structlog.get_logger(__name__)

if FLAG__ENABLE_EMAIL and SES_ACCESS_KEY_ID and SES_SECRET_ACCESS_KEY and SES_REGION:
    session = boto3.session.Session()
    SES_CLIENT = session.client(
        "sesv2",
        aws_access_key_id=SES_ACCESS_KEY_ID,
        aws_secret_access_key=SES_SECRET_ACCESS_KEY,
        region_name=SES_REGION,
    )
else:
    SES_CLIENT = None


def send_email_notification(
        to_email, subject, body_text=None, body_html=None, from_user=None
):
    if SES_CLIENT is None:
        raise RuntimeError(
            "Email is not enabled. To enable email, ensure FLAG__ENABLE_EMAIL is True "
            "and SES_ACCESS_KEY_ID, SES_SECRET_ACCESS_KEY, and SES_REGION are set."
        )

    if from_user is None and SES_FROM_EMAIL is None:
        raise ValueError(
            "Sender email is not configured. Provide from_user or set SES_FROM_USER."
        )
    else:
        from_email = f"{from_user}@{SES_DOMAIN}" if from_user else SES_FROM_EMAIL

    if body_text is None and body_html is None:
        raise ValueError("At least one of body_text or body_html must be provided.")

    body = {}
    if body_text is not None:
        body["Text"] = {"Data": body_text}
    if body_html is not None:
        body["Html"] = {"Data": body_html}

    try:
        response = SES_CLIENT.send_email(
            FromEmailAddress=from_email,
            Destination={"ToAddresses": [to_email]},
            Content={
                "Simple": {
                    "Subject": {"Data": subject},
                    "Body": {**body},
                }
            },
        )
    except Exception as e:
        logger.error(
            "SES email send failed",
            subject=subject,
            to_email=to_email,
            from_email=from_email,
            error=str(e),
        )
        return response

    message_id = response.get("MessageId", "unknown")
    logger.info(
        "SES email sent",
        subject=subject,
        to_email=to_email,
        from_email=from_email,
        message_id=message_id,
    )

    return response
