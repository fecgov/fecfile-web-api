import logging
from io import StringIO

import boto3
import numpy as np
import pandas as pd
import psycopg2
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from pandas_schema import Column, Schema
from pandas_schema.validation import MatchesPatternValidation, InListValidation
from rest_framework import status
from rest_framework.decorators import api_view

from fecfiler.authentication.authorization import is_read_only_or_filer_reports
from fecfiler.contacts.views.duplicate import create_temp_db_model
from fecfiler.contacts.views.merge import (
    create_temp_contact_table,
    create_temp_transaction_association_model,
)
from fecfiler.core.views import (
    get_comittee_id,
    NoOPError,
    get_next_entity_id,
    check_null_value,
)
from fecfiler.settings import AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME

logger = logging.getLogger(__name__)


def reorder_user_data(contacts_added, contact_list):
    try:
        contacts_added.columns = [
            "cmte_id",
            "entity_type",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip_code",
            "employer",
            "occupation",
            "entity_name",
            "last_name",
            "first_name",
            "middle_name",
            "preffix",
            "suffix",
            "cand_office",
            "cand_office_state",
            "cand_office_district",
            "ref_cand_cmte_id",
            "transaction_id",
        ]

        if contact_list is not None:
            contacts_list_dict = pd.DataFrame.from_records(contact_list)
            contacts_list_dict["street_1"] = contacts_list_dict["street_1"].str.strip()
            contacts_list_dict.zip_code = contacts_list_dict.zip_code.astype(str)
            contacts_added.reset_index(drop=True, inplace=True)

            # json_added = contacts_added.to_json(orient='records')
            # json_contact = contacts_list_dict.to_json(orient='records')
            # contacts_added_dict = pd.read_json(json_added)
            contacts_added_dict = contacts_added
            # contact_list_dict = pd.read_json(json_contact)
            contact_list_dict = contacts_list_dict
            contact_list_dict.fillna(value=pd.np.nan, inplace=True)
            contacts_added_dict = contacts_added_dict[
                contacts_added_dict.zip_code.notnull()
            ]
            contact_list_dict1 = contact_list_dict.replace(np.nan, "", regex=True)
            contacts_added_dict1 = contacts_added_dict.replace(np.nan, "", regex=True)
            contacts_added_dict1 = contacts_added_dict1[
                contacts_added_dict1.zip_code.notnull()
            ]
            # contacts_added_dict1.drop(contacts_added_dict1.loc[contacts_added_dict1['zip_code']
            # != ''].index, inplace=True)
            # contacts_added_dict1.zip_code = contacts_added_dict1.zip_code.astype(int)
            contacts_added_dict1.zip_code = contacts_added_dict1.zip_code.astype(str)
            contacts_added_dict1.reset_index(drop=True, inplace=True)

            contact_list_dict1.zip_code = contact_list_dict1.zip_code.astype(str)

            contact_final_dict = contacts_added_dict1.merge(
                contact_list_dict1,
                how="outer",
                on=[
                    "cmte_id",
                    "entity_type",
                    "street_1",
                    "street_2",
                    "city",
                    "state",
                    "zip_code",
                    "employer",
                    "occupation",
                    "entity_name",
                    "last_name",
                    "first_name",
                    "middle_name",
                    "preffix",
                    "suffix",
                    "cand_office",
                    "cand_office_state",
                    "cand_office_district",
                    "ref_cand_cmte_id",
                ],
                indicator=True,
            ).loc[lambda x: x["_merge"] == "left_only"]

            contact_duplicate_dict = contacts_added_dict1.merge(
                contact_list_dict1,
                how="inner",
                on=[
                    "cmte_id",
                    "entity_type",
                    "street_1",
                    "street_2",
                    "city",
                    "state",
                    "zip_code",
                    "employer",
                    "occupation",
                    "entity_name",
                    "last_name",
                    "first_name",
                    "middle_name",
                    "preffix",
                    "suffix",
                    "cand_office",
                    "cand_office_state",
                    "cand_office_district",
                    "ref_cand_cmte_id",
                ],
                indicator=False,
            )
            print(type(contact_duplicate_dict))
            del contact_final_dict["_merge"]
            data = {
                "final_contact_df": contact_final_dict,
                "duplicate_contact_df": contact_duplicate_dict,
            }
        else:
            contacts_added.reset_index(drop=True, inplace=True)
            json_added = contacts_added.to_json(orient="records")
            contacts_added_dict = pd.read_json(json_added)
            contacts_added_dict = contacts_added_dict[
                contacts_added_dict.zip_code.notnull()
            ]
            contacts_added_dict.zip_code = contacts_added_dict.zip_code.astype(str)
            contacts_added_dict1 = contacts_added_dict.replace(np.nan, "", regex=True)
            data = {
                "final_contact_df": contacts_added_dict1,
                "duplicate_contact_df": "",
            }
        return data
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Exception occurred while reformatting the data.")


def create_db_model(contacts_final_dict, file_name):
    try:
        contacts_final_dict = contacts_final_dict.to_dict(orient="records")
        for contact in contacts_final_dict:
            print(contact)
        with connection.cursor() as cursor:
            all_contact = [
                {
                    **contact,
                    "entity_id": get_next_entity_id(contact["entity_type"]),
                    "file_name": file_name,
                }
                for contact in contacts_final_dict
            ]

            psycopg2.extras.execute_batch(
                cursor,
                """
                INSERT INTO public.entity (
                    entity_id, cmte_id, entity_type, entity_name, first_name,
                    last_name, middle_name, preffix, suffix, street_1, street_2,
                    city, state, zip_code, occupation, employer, cand_office,
                    cand_office_state, cand_office_district, ref_cand_cmte_id)
                VALUES (
                    %(entity_id)s,
                    %(cmte_id)s,
                    %(entity_type)s,
                    %(entity_name)s,
                    %(first_name)s,
                    %(last_name)s,
                    %(middle_name)s,
                    %(preffix)s,
                    %(suffix)s,
                    %(street_1)s,
                    %(street_2)s,
                    %(city)s,
                    %(state)s,
                    %(zip_code)s,
                    %(occupation)s,
                    %(employer)s,
                    %(cand_office)s,
                    %(cand_office_state)s,
                    %(cand_office_district)s,
                    %(ref_cand_cmte_id)s
                );
                """,
                all_contact,
            )

        cursor.close()
        return all_contact
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts to database.")


def get_contact_list(cmte_id):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT entity_id as duplicate_entity, cmte_id, entity_type, street_1, street_2,
            city, state, zip_code, employer, occupation, entity_name, last_name, first_name,
            middle_name, preffix, suffix, cand_office, cand_office_state, cand_office_district,
            ref_cand_cmte_id
            FROM public.entity WHERE cmte_id = %s AND entity_type not in ('IND', 'ORG')
            AND delete_ind is distinct from 'Y'
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id]
            )
            contact_list = cursor.fetchall()
            if not contact_list:
                raise NoOPError("No entity found for cmte_id {} ".format(cmte_id))
            merged_list = []
            for dictL in contact_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        raise e


def save_contact_db(contacts_added, cmte_id, file_name):
    all_contact = []
    contact_list = get_contact_list(cmte_id)
    data = reorder_user_data(contacts_added, contact_list)
    all_contact = create_db_model(data.get("final_contact_df"), file_name)
    table_name = create_temp_contact_table(file_name)
    create_temp_transaction_association_model(all_contact, table_name)

    duplicate_contact_df = data.get("duplicate_contact_df")
    # duplicate_contact_df['duplicate_entity'] = ''
    duplicate_contact_df["transaction_id"] = ""
    duplicate_contact_df["file_selected"] = "true"
    duplicate_contact_df["file_name"] = file_name
    duplicate_contact_dict = duplicate_contact_df.to_dict("records")

    create_temp_db_model(duplicate_contact_dict, file_name, cmte_id)

    return len(all_contact), len(data.get("duplicate_contact_df"))


def custom_validate_cand_df(uploaded_df_orig, cmte_id):
    try:

        uploaded_df_orig.ZIP_CODE = uploaded_df_orig.ZIP_CODE.astype(str)

        uploaded_df_orig = uploaded_df_orig.replace(np.nan, "", regex=True)
        uploaded_df = uploaded_df_orig.drop_duplicates()

        uploaded_df_duplicates = uploaded_df_orig[
            uploaded_df_orig.duplicated(keep=False)
        ]
        uploaded_df_duplicates = uploaded_df_duplicates.drop_duplicates()

        uploaded_df_cmt = uploaded_df[
            uploaded_df.COMMITTEE_ID.str.contains(cmte_id, case=False)
        ]
        uploaded_df_cmt_error = pd.concat(
            [uploaded_df, uploaded_df_cmt]
        ).drop_duplicates(keep=False)

        data_clean = uploaded_df_cmt.replace(r"^\s+$", np.NaN, regex=True)

        data = {"final_list": data_clean}

        return data

    except Exception as e:
        logger.debug(e)
        raise NoOPError(
            "Error occurred while applying custom validation. Please ensure header and data values are in "
            "proper format."
        )


@api_view(["POST"])
def upload_cand_contact(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == "POST":
                cmte_id = get_comittee_id(request.user.username)
                client = boto3.client(
                    "s3", settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
                )
                bucket = AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME
                file_name = request.data.get("file_name")
                s3_file_name = file_name.lower()
                s3_file_name = "contacts/" + cmte_id + "_" + s3_file_name
                csv_obj = client.get_object(Bucket=bucket, Key=s3_file_name)
                body = csv_obj["Body"]
                csv_string = body.read().decode("latin")

                df = pd.read_csv(StringIO(csv_string), dtype=object)

                df = df[
                    [
                        "COMMITTEE_ID",
                        "ENTITY_TYPE",
                        "STREET_1",
                        "STREET_2",
                        "CITY",
                        "STATE",
                        "ZIP_CODE",
                        "EMPLOYER",
                        "OCCUPATION",
                        "ORGANIZATION_NAME",
                        "LAST_NAME",
                        "FIRST_NAME",
                        "MIDDLE_NAME",
                        "PREFIX",
                        "SUFFIX",
                        "CAND_OFFICE",
                        "CAND_OFFICE_STATE",
                        "CAND_OFFICE_DISTRICT",
                        "REF_CAND_CMTE_ID",
                        "TRANSACTION_ID",
                    ]
                ]

                df.columns = [
                    "COMMITTEE_ID",
                    "ENTITY_TYPE",
                    "STREET_1",
                    "STREET_2",
                    "CITY",
                    "STATE",
                    "ZIP_CODE",
                    "EMPLOYER",
                    "OCCUPATION",
                    "ORGANIZATION_NAME",
                    "LAST_NAME",
                    "FIRST_NAME",
                    "MIDDLE_NAME",
                    "PREFFIX",
                    "SUFFIX",
                    "CAND_OFFICE",
                    "CAND_OFFICE_STATE",
                    "CAND_OFFICE_DISTRICT",
                    "REF_CAND_CMTE_ID",
                    "TRANSACTION_ID",
                ]

                df = df[~df["ENTITY_TYPE"].isin(["ORG", "IND"])]
                # test_data_org = df.ENTITY_TYPE.str.contains('ORG', case=False)
                # test_data_org1 = df[test_data_org]
                # test_data_ind = df.ENTITY_TYPE.str.contains('IND', case=False)
                # test_data_ind1 = df[test_data_ind]
                # df = pd.concat([test_data_org1, test_data_ind1]).reset_index(drop=True)

                print(df.head())
                file_name = file_name[(file_name.rfind("/") + 1):]

                data = custom_validate_cand_df(df, cmte_id)

                contacts_added = data.get("final_list")

                save_data_len, duplicate_len = save_contact_db(
                    contacts_added, cmte_id, file_name
                )

                contacts_temp = {
                    "contacts_saved": save_data_len,
                    "duplicate": duplicate_len,
                }
                contacts = {"Response": contacts_temp}

                return JsonResponse(
                    contacts, status=status.HTTP_201_CREATED, safe=False
                )

        except Exception as e:
            json_result = {"message": str(e)}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)
