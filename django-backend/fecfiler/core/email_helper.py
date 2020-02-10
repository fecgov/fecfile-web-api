import logging
import maya

# from functools import lru_cache
from django.db import connection
from django.template.loader import render_to_string
import boto3
from botocore.exceptions import ClientError

# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
# import datetime

logger = logging.getLogger(__name__)


def email(boolean, data):
    SENDER = "donotreply@fec.gov"
    RECIPIENT = []

    # print(data.get('email_on_file_1'))
    if "email_on_file" in data and (
        not (
            data.get("email_on_file") == "-"
            or data.get("email_on_file") is None
            or data.get("email_on_file") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("email_on_file"))

    if "email_on_file_1" in data and (
        not (
            data.get("email_on_file_1") == "-"
            or data.get("email_on_file_1") is None
            or data.get("email_on_file_1") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("email_on_file_1"))

    if "email_on_file_2" in data and (
        not (
            data.get("email_on_file_2") == "-"
            or data.get("email_on_file_2") is None
            or data.get("email_on_file_2") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("email_on_file_2"))

    if "email_1" in data and (
        not (
            data.get("email_1") == "-"
            or data.get("email_1") is None
            or data.get("email_1") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("email_1"))

    if "email_2" in data and (
        not (
            data.get("email_2") == "-"
            or data.get("email_2") is None
            or data.get("email_2") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("email_2"))

            # print(data.get('additional_email_1'))
    if "additional_email_1" in data and (
        not (
            data.get("additional_email_1") == "-"
            or data.get("additional_email_1") is None
            or data.get("additional_email_1") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("additional_email_1"))

    # print(data.get('additional_email_2'))
    if "additional_email_2" in data and (
        not (
            data.get("additional_email_2") == "-"
            or data.get("additional_email_2") is None
            or data.get("additional_email_2") == "null"
        )
    ):
        RECIPIENT.append("%s" % data.get("additional_email_2"))

    logger.debug('***here is a list of email recipients:{}'.format(RECIPIENT))
    SUBJECT = "Form {} submitted successfully".format(data.get("form_type"))

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (
        "Form 3X that we received has been validated and submitted\r\n"
        "This email was sent by FEC.gov. If you are receiving this email in error or have any questions, please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307."
    )

    # The HTML body of the email.
    # final_html = email_ack1.html.replace('{{@REPID}}',1234567).replace('{{@REPLACE_CMTE_ID}}',C0123456)
    # t = Template(email_ack1)
    # c= Context({'@REPID':123458},)

    # data["updated_at"] = (
    #     maya.parse(data["updated_at"])
    #     .datetime(to_timezone="US/Eastern", naive=True)
    #     .strftime("%m-%d-%Y %T")
    # )
    # data["created_at"] = (
    #     maya.parse(data["created_at"])
    #     .datetime(to_timezone="US/Eastern", naive=True)
    #     .strftime("%m-%d-%Y %T")
    # )
    BODY_HTML = render_to_string("email_ack.html", {"data": data})
    # data.get('committeeid')

    """<html>
    <head></head>
    <body>
      <h1>Form 99 that we received has been validated and submitted</h1>
      <p>This email was sent by FEC.gov. If you are receiving this email in error or have any questions, please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307."</p>
    </body>
    </html>"""

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client("ses", region_name="us-east-1")

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={"ToAddresses": RECIPIENT},
            Message={
                "Body": {
                    "Html": {"Charset": CHARSET, "Data": BODY_HTML},
                    "Text": {"Charset": CHARSET, "Data": BODY_TEXT},
                },
                "Subject": {"Charset": CHARSET, "Data": SUBJECT},
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response["Error"]["Message"])
