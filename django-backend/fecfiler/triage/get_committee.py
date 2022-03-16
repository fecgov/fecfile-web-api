from django.db import connection
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


def get_comittee_id(username):
    cmte_id = ""
    if len(username) > 9:
        cmte_id = username[0:9]

    return cmte_id


def get_levin_accounts(cmte_id):
    """
    load levin_account names and account ids for a committee
    """
    _sql = """
    select json_agg(t) from
    (select levin_account_id, levin_account_name
    from levin_account where cmte_id = %s
    and delete_ind is distinct from 'Y') t
    """
    try:
        with connection.cursor() as cursor:
            # INSERT row into Reports table
            cursor.execute(_sql, [cmte_id])
            return cursor.fetchone()[0]
    except Exception as e:
        logger.debug("Error on loading levin account names:" + str(e))
        raise


def get_committee_details(request):
    try:
        print(f"HULLO {request.user}")
        cmte_id = get_comittee_id(request.user.username)
        with connection.cursor() as cursor:
            # GET all rows from committee table
            query_string = """SELECT cm.cmte_id AS "committeeid",
                cm.cmte_name AS "committeename", cm.street_1 AS "street1",
                cm.street_2 AS "street2",
                cm.city, cm.state, cm.zip_code AS "zipcode",
                cm.cmte_email_1 AS "email_on_file",
                cm.cmte_email_2 AS "email_on_file_1",
                cm.phone_number, cm.cmte_type, cm.cmte_dsgn,
                cm.cmte_filing_freq, cm.cmte_filed_type,
                cm.treasurer_last_name AS "treasurerlastname",
                cm.treasurer_first_name AS "treasurerfirstname",
                cm.treasurer_middle_name AS "treasurermiddlename",
                cm.treasurer_prefix AS "treasurerprefix",
                cm.treasurer_suffix AS "treasurersuffix",
                cm.create_date AS "created_at", cm.cmte_type_category, f1.fax,
                f1.tphone as "treasurerphone", f1.url as "website",
                f1.email as "treasureremail"
                FROM public.committee_master cm
                LEFT JOIN public.form_1 f1 ON f1.comid=cmte_id
                WHERE cm.cmte_id = %s
                ORDER BY cm.create_date, f1.sub_date DESC, f1.create_date DESC LIMIT 1
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id]
            )
            modified_output = cursor.fetchone()[0]
        if modified_output is None:
            raise Exception(
                "The Committee ID: {} does not match records in Committee table".format(
                    cmte_id
                )
            )
        levin_accounts = get_levin_accounts(cmte_id)
        modified_output[0]["levin_accounts"] = levin_accounts
        return HttpResponse(modified_output[0], status=200)
    except Exception as e:
        return HttpResponse(
            "The get_committee_details API is throwing  an error: " + str(e),
            status=400,
        )
