import logging
from io import StringIO

import boto3
import numpy
import numpy as np
import pandas
import pandas as pd
import psycopg2
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from pandas_schema import Column, Schema
from pandas_schema.validation import (
    MatchesPatternValidation,
    InListValidation,
    CustomElementValidation,
)
from rest_framework import status
from rest_framework.decorators import api_view

from fecfiler.authentication.authorization import is_read_only_or_filer_reports


from fecfiler.contacts.views.merge import (
    check_if_all_options_selected,
    create_temp_contact_table,
    create_temp_transaction_association_model,
)
from fecfiler.core.views import (
    get_comittee_id,
    NoOPError,
    get_next_entity_id,
    check_null_value,
    partial_match,
    get_list_contact,
    set_offset_n_fetch,
    get_num_of_pages,
)
from fecfiler.settings import (
    AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME,
    CONTACT_MATCH_PERCENTAGE,
)

logger = logging.getLogger(__name__)


def check_int(num):
    try:
        int(num)
    except ValueError:
        return False
    return True


def check_range(num, range_val):
    if 0 < len(str(num)) <= range_val:
        return True
    return False


def check_length_less(num, range_val):
    if len(str(num)) <= range_val:
        return True
    return False


def check_length(num, range_val):
    if len(str(num)) > 0 and len(str(num)) == range_val:
        return True
    return False


int_validation = [CustomElementValidation(lambda i: check_int(i), "is not integer")]
null_validation = [
    CustomElementValidation(lambda d: d is not np.nan, "this field cannot be null")
]
int_street_range_check = [
    CustomElementValidation(
        lambda d: check_range(d, 34), "length is not between 1 and 34"
    )
]
int_city_range_check = [
    CustomElementValidation(
        lambda d: check_range(d, 30), "length is not between 1 and 30"
    )
]
int_zip_range_check = [
    CustomElementValidation(
        lambda d: check_range(d, 9), "length is not between 1 and 9"
    )
]
int_street_2_range = [
    CustomElementValidation(
        lambda d: check_length_less(d, 34), "length is not more than 34"
    )
]
int_state_range_check = [
    CustomElementValidation(lambda d: check_length(d, 2), "length is not equal to 2")
]
int_emp_check = [
    CustomElementValidation(
        lambda d: check_length_less(d, 38), "length is more than 38"
    )
]
int_org_check = [
    CustomElementValidation(
        lambda d: check_length_less(d, 200), "length is more than 200"
    )
]
int_name_check = [
    CustomElementValidation(
        lambda d: check_length_less(d, 20), "length is more than 20"
    )
]
int_prefix_name = [
    CustomElementValidation(
        lambda d: check_length_less(d, 10), "length is more than 10"
    )
]


def schema_validation(uploaded_df, cmte_id, transaction_included, file_name):
    try:
        if not transaction_included:
            schema = Schema(
                [
                    Column("COMMITTEE_ID", [MatchesPatternValidation("[cC][0-9]{8}")]),
                    Column("ENTITY_TYPE", [InListValidation(["IND", "ORG"])]),
                    Column("STREET_1", int_street_range_check + null_validation),
                    Column("STREET_2", int_street_2_range),
                    Column("CITY", int_city_range_check + null_validation),
                    Column("STATE", int_state_range_check),
                    Column("ZIP", int_zip_range_check + null_validation),
                    Column("EMPLOYER", int_emp_check),
                    Column("OCCUPATION", int_emp_check),
                    Column("ORGANIZATION_NAME", int_org_check),
                    Column("LASTNAME", int_city_range_check),
                    Column("FIRSTNAME", int_name_check),
                    Column("MIDDLENAME", int_name_check),
                    Column("PREFIX", int_prefix_name),
                    Column("SUFFIX", int_prefix_name),
                ]
            )

            errors = schema.validate(uploaded_df)

            errors_index_rows = [e.row for e in errors]
            error_dict = {}
            error_list = []
            i = 0
            for e in errors:
                i += 1
                error_list.append(
                    {
                        "error_id": i,
                        "row_no": e.row,
                        "field_name": e.column,
                        "msg": e.message,
                    }
                )

            data_clean = uploaded_df.drop(index=errors_index_rows)

            test_data_ind = data_clean.ENTITY_TYPE.str.contains("IND", case=False)
            test_data_ind1 = data_clean[test_data_ind]

            test_data_ind_temp = (
                test_data_ind_diff
            ) = test_data_org_temp = test_data_org_diff = pd.DataFrame(
                columns=[
                    "COMMITTEE_ID",
                    "ENTITY_TYPE",
                    "STREET_1",
                    "STREET_2",
                    "CITY",
                    "STATE",
                    "ZIP",
                    "EMPLOYER",
                    "OCCUPATION",
                    "ORGANIZATION_NAME",
                    "LASTNAME",
                    "FIRSTNAME",
                    "MIDDLENAME",
                    "PREFIX",
                    "SUFFIX",
                ]
            )

            if not test_data_ind1.empty:
                test_data_ind_temp = test_data_ind1.dropna(
                    how="any", subset=["LASTNAME", "FIRSTNAME"]
                )
                test_data_ind_diff = pd.concat(
                    [test_data_ind1, test_data_ind_temp]
                ).drop_duplicates(keep=False)

                for index, row in test_data_ind_diff.iterrows():
                    error_list.append(
                        {
                            "error_id": i,
                            "row_no": index,
                            "field_name": "FIRST_NAME or LAST_NAME",
                            "msg": "FIRST_NAME and LAST_NAME cannot be empty if ENTITY_TYPE is IND",
                        }
                    )

            test_data_org = data_clean.ENTITY_TYPE.str.contains("ORG", case=False)
            test_data_org1 = data_clean[test_data_org]

            if not test_data_org1.empty:
                test_data_org_temp = test_data_org1.dropna(
                    how="any", subset=["ORGANIZATION_NAME"]
                )
                test_data_org_diff = pd.concat(
                    [test_data_org1, test_data_org_temp]
                ).drop_duplicates(keep=False)

                for index, row in test_data_org_diff.iterrows():
                    error_list.append(
                        {
                            "error_id": i,
                            "row_no": index,
                            "field_name": "ORGANIZATION_NAME",
                            "msg": "ORGANIZATION_NAME cannot be empty if ENTITY_TYPE is ORG",
                        }
                    )

            test_data_final = pd.concat(
                [test_data_ind_temp, test_data_org_temp]
            ).reset_index(drop=True)

            # uncomment when test is done
            if len(error_list) > 0:
                data_clean = []
                data = {
                    "errors": error_list,
                    "data_clean": data_clean,
                    "duplicate_db_count": 0,
                }
                return data

            test_data_final1 = test_data_final.replace(np.nan, "", regex=True)
            uploaded_df_cmt = test_data_final1[
                test_data_final1.COMMITTEE_ID.str.contains(cmte_id, case=False)
            ]
            uploaded_df_cmt_error = pd.concat(
                [test_data_final1, uploaded_df_cmt]
            ).drop_duplicates(keep=False)
            test_data_final1 = uploaded_df_cmt

        else:
            test_data_final1 = uploaded_df.replace(np.nan, "", regex=True)

        # contacts_list_dict = pd.DataFrame.from_records(get_contact_list(cmte_id))
        contact_list = get_contact_list(cmte_id)

        if contact_list is None:
            contact_list = []

        compare_total_address_list = []
        compare_entity_id_list = []
        potential_duplicate = []

        for contact in contact_list:
            compare_entity_id_list.append(contact.get("entity_id"))
            compare_total_address_list.append(
                " ".join(
                    filter(
                        None,
                        [
                            contact.get("entity_name"),
                            contact.get("preffix"),
                            contact.get("first_name"),
                            contact.get("middle_name"),
                            contact.get("last_name"),
                            contact.get("suffix"),
                            contact.get("street_1"),
                            contact.get("street_2"),
                            contact.get("city"),
                            contact.get("state"),
                            contact.get("zip_code"),
                            contact.get("occupation"),
                            contact.get("employer"),
                        ],
                    )
                )
            )

        if len(compare_total_address_list) == 0:
            for index, row in test_data_final1.iterrows():
                temp_data = {
                    "entity_type": row["ENTITY_TYPE"],
                    "cmte_id": row["COMMITTEE_ID"],
                    "entity_name": row["ORGANIZATION_NAME"],
                    "first_name": row["FIRSTNAME"],
                    "last_name": row["LASTNAME"],
                    "middle_name": row["MIDDLENAME"],
                    "preffix": row["PREFIX"],
                    "suffix": row["SUFFIX"],
                    "street_1": row["STREET_1"],
                    "street_2": row["STREET_2"],
                    "city": row["CITY"],
                    "state": row["STATE"],
                    "zip_code": row["ZIP"],
                    "occupation": row["OCCUPATION"],
                    "employer": row["EMPLOYER"],
                    "duplicate_entity": "",
                    "file_selected": "true",
                    "file_name": file_name,
                    "transaction_id": "",
                }
                if transaction_included:
                    temp_data["transaction_id"] = row["TRANSACTION_ID"]
                potential_duplicate.append(temp_data)

        # traverse row by row bases
        file_record = []
        exact_match = []
        moderation_score = CONTACT_MATCH_PERCENTAGE
        if len(contact_list) > 0:
            for index, row in test_data_final1.iterrows():
                input_list = [
                    row["ORGANIZATION_NAME"],
                    row["PREFIX"],
                    row["FIRSTNAME"],
                    row["MIDDLENAME"],
                    row["LASTNAME"],
                    row["SUFFIX"],
                ]
                input_name = " ".join(filter(None, input_list))
                input_address = " ".join(
                    filter(
                        None,
                        [
                            row["STREET_1"],
                            row["STREET_2"],
                            row["CITY"],
                            row["STATE"],
                            row["ZIP"],
                        ],
                    )
                )
                input_total_address_list = [
                    " ".join(
                        [
                            input_name,
                            input_address,
                            row["OCCUPATION"],
                            row["EMPLOYER"],
                        ]
                    )
                ]

                inputcolumn = pandas.DataFrame(input_total_address_list)
                inputcolumn.columns = ["Match"]
                compare_dict = {
                    "EntityId": compare_entity_id_list,
                    "Compare": compare_total_address_list,
                }
                comparecolumn = pandas.DataFrame(compare_dict)

                inputcolumn["Key"] = 1
                comparecolumn["Key"] = 1
                combined_dataframe = comparecolumn.merge(
                    inputcolumn, on="Key", how="left"
                )

                partial_match_vector = numpy.vectorize(partial_match)
                combined_dataframe["Score"] = partial_match_vector(
                    combined_dataframe["Match"], combined_dataframe["Compare"]
                )
                combined_dataframe = combined_dataframe[
                    combined_dataframe.Score >= moderation_score
                ]

                score_val = combined_dataframe["Score"].values.tolist()
                if combined_dataframe.empty:

                    temp_data = {
                        "entity_type": row["ENTITY_TYPE"],
                        "cmte_id": row["COMMITTEE_ID"],
                        "entity_name": row["ORGANIZATION_NAME"],
                        "first_name": row["FIRSTNAME"],
                        "last_name": row["LASTNAME"],
                        "middle_name": row["MIDDLENAME"],
                        "preffix": row["PREFIX"],
                        "suffix": row["SUFFIX"],
                        "street_1": row["STREET_1"],
                        "street_2": row["STREET_2"],
                        "city": row["CITY"],
                        "state": row["STATE"],
                        "zip_code": row["ZIP"],
                        "occupation": row["OCCUPATION"],
                        "employer": row["EMPLOYER"],
                        "duplicate_entity": "",
                        "file_selected": "true",
                        "file_name": file_name,
                        "transaction_id": "",
                    }
                    if transaction_included:
                        temp_data["transaction_id"] = row["TRANSACTION_ID"]
                    potential_duplicate.append(temp_data)

                elif 100 in score_val:
                    print("Got 100% match in DB. Removing record index.", index)
                    exact_match.append(index)
                    continue

                else:
                    duplicate_list = get_list_contact(
                        cmte_id, combined_dataframe["EntityId"].values.tolist()
                    )
                    joined_string = ",".join(
                        combined_dataframe["EntityId"].values.tolist()
                    )

                    temp_data = {
                        "entity_type": row["ENTITY_TYPE"],
                        "cmte_id": row["COMMITTEE_ID"],
                        "entity_name": row["ORGANIZATION_NAME"],
                        "first_name": row["FIRSTNAME"],
                        "last_name": row["LASTNAME"],
                        "middle_name": row["MIDDLENAME"],
                        "preffix": row["PREFIX"],
                        "suffix": row["SUFFIX"],
                        "street_1": row["STREET_1"],
                        "street_2": row["STREET_2"],
                        "city": row["CITY"],
                        "state": row["STATE"],
                        "zip_code": row["ZIP"],
                        "occupation": row["OCCUPATION"],
                        "employer": row["EMPLOYER"],
                        "duplicate_entity": joined_string,
                        "file_selected": "",
                        "file_name": file_name,
                        "transaction_id": "",
                    }
                    if transaction_included:
                        temp_data["transaction_id"] = row["TRANSACTION_ID"]
                    potential_duplicate.append(temp_data)

        create_temp_db_model(potential_duplicate, file_name, cmte_id)

        data = {
            "errors": error_list,
            "data_clean": data_clean,
            "duplicate_db_count": len(exact_match),
        }
        return data
    except Exception as e:
        logger.debug(e)
        raise NoOPError(
            "Error occurred while validating file structure. Please ensure header and data values are in "
            "proper format." + str(e)
        )


def get_next_temp_entity_id():
    default_sequence = 1
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT max(entity_id) from public.entity_import_temp""")
            user_id = cursor.fetchone()[0]
            if user_id is None:
                default_sequence
            else:
                default_sequence = int(user_id) + 1

        return default_sequence
    except Exception:
        raise


def create_temp_db_model(contacts_final_dict, file_name, cmte_id):
    try:
        count = get_temp_count(cmte_id, file_name)
        if count > 0:
            delete_import(cmte_id, file_name)

        with connection.cursor() as cursor:
            all_contact = [
                {
                    **contact,
                }
                for contact in contacts_final_dict
            ]

            psycopg2.extras.execute_batch(
                cursor,
                """
                INSERT INTO public.entity_import_temp (
                    cmte_id, entity_type, entity_name, first_name, last_name,
                    middle_name, preffix, suffix, street_1, street_2, city, state,
                    zip_code, occupation, employer, duplicate_entity, transaction_id,
                    file_name, file_selected
                ) VALUES (
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
                    %(duplicate_entity)s,
                    %(transaction_id)s,
                    %(file_name)s,
                    %(file_selected)s
                );
                """,
                all_contact,
            )

        cursor.close()
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts to database.")


def get_contact_list(cmte_id):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT entity_id, street_1, street_2, city, state, zip_code,
            employer, occupation, entity_name, last_name, first_name, middle_name,
            preffix, suffix
            FROM public.entity
            WHERE cmte_id = %s AND entity_type in ('IND', 'ORG') AND delete_ind is distinct from 'Y'
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


def get_temp_contact_list(cmte_id, file_name):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT entity_id, cmte_id, transaction_id, file_name, entity_type, street_1,
            street_2, city, state, zip_code, employer, occupation, entity_name, last_name,
            first_name, middle_name, preffix, suffix
            FROM public.entity_import_temp
            WHERE cmte_id = %s AND file_name = %s
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                [cmte_id, file_name],
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


def get_temp_contact_pagination_list(cmte_id, file_name, page_num, itemsperpage):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT entity_id, cmte_id, transaction_id, duplicate_entity, file_selected, update_db,
            exsisting_db, file_name, entity_type, street_1, street_2, city, state, zip_code,employer,
            occupation,entity_name, last_name, first_name, middle_name, preffix, suffix
            FROM public.entity_import_temp
            WHERE cmte_id = %s AND file_name = %s AND duplicate_entity NOT IN ('', ' ')
            ORDER BY entity_id ASC
            """
            trans_query_string = set_offset_n_fetch(
                query_string, page_num, itemsperpage
            )
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + trans_query_string + """) t""",
                [cmte_id, file_name],
            )
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj = data_row[0]
            if forms_obj is None:
                forms_obj = []

        return forms_obj
    except Exception as e:
        raise e


def get_total_count(cmte_id, file_name):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT count(*)
            FROM public.entity_import_temp
            WHERE cmte_id = %s AND file_name = %s AND duplicate_entity NOT IN ('', ' ')
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                [cmte_id, file_name],
            )
            row1 = cursor.fetchone()[0]
            list(row1)
            totalcount = row1[0]["count"]

        return totalcount
    except Exception as e:
        raise e


def get_temp_count(cmte_id, file_name):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT count(*)
            FROM public.entity_import_temp
            WHERE cmte_id = %s AND file_name = %s
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                [cmte_id, file_name],
            )
            row1 = cursor.fetchone()[0]
            list(row1)
            totalcount = row1[0]["count"]

        return totalcount
    except Exception as e:
        raise e


def custom_validate_df(uploaded_df_orig, cmte_id, transaction_included, file_name):
    try:

        uploaded_df_orig.ZIP = uploaded_df_orig.ZIP.astype(str)

        uploaded_df = uploaded_df_orig.drop_duplicates()
        uploaded_df_duplicates = uploaded_df_orig[
            uploaded_df_orig.duplicated(keep=False)
        ]
        uploaded_df_duplicates = uploaded_df_duplicates.drop_duplicates()

        schema_data = schema_validation(
            uploaded_df, cmte_id, transaction_included, file_name
        )
        errors = schema_data.get("errors")

        response = {
            "error_list": errors,
            "duplcate_file_count": len(uploaded_df_duplicates),
            "duplicate_db_count": schema_data.get("duplicate_db_count"),
        }
        return response

    except Exception as e:
        logger.debug(e)
        raise NoOPError(
            "Error occurred while applying custom validation. Please ensure header and data values are in "
            "proper format."
        )


@api_view(["POST"])
def validate_contact(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == "POST":
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")

                # log the import
                sql = """
                    insert into public.entity_import_log (
                        committee_id, file_name, uploaded_by, uploaded_on, checksum
                    ) values (
                        %(cmte_id)s, %(file_name)s, %(uploaded_by)s, now(), 'N/A'
                    )
                """
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "cmte_id": cmte_id,
                            "file_name": file_name,
                            "uploaded_by": request.user.username[9:],
                        },
                    )

                client = boto3.client(
                    "s3", settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
                )
                bucket = AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME
                transaction_included = request.data.get("transaction_included")
                csv_obj = client.get_object(
                    Bucket=bucket, Key="contacts/" + cmte_id + "/" + file_name
                )
                body = csv_obj["Body"]
                csv_string = body.read().decode("latin")

                df = pd.read_csv(StringIO(csv_string), dtype=object)

                df = df[
                    [
                        "COMMITTEE ID",
                        "ENTITY TYPE",
                        "STREET 1",
                        "STREET 2",
                        "CITY",
                        "STATE",
                        "ZIP",
                        "EMPLOYER",
                        "OCCUPATION",
                        "ORGANIZATION NAME",
                        "LAST NAME",
                        "FIRST NAME",
                        "MIDDLE NAME",
                        "PREFIX",
                        "SUFFIX",
                    ]
                ]

                df.columns = [
                    "COMMITTEE_ID",
                    "ENTITY_TYPE",
                    "STREET_1",
                    "STREET_2",
                    "CITY",
                    "STATE",
                    "ZIP",
                    "EMPLOYER",
                    "OCCUPATION",
                    "ORGANIZATION_NAME",
                    "LASTNAME",
                    "FIRSTNAME",
                    "MIDDLENAME",
                    "PREFIX",
                    "SUFFIX",
                ]

                if transaction_included:
                    test_data_org = df.ENTITY_TYPE.str.contains("ORG", case=False)
                    test_data_org1 = df[test_data_org]
                    test_data_ind = df.ENTITY_TYPE.str.contains("IND", case=False)
                    test_data_ind1 = df[test_data_ind]
                    df = pd.concat([test_data_org1, test_data_ind1]).reset_index(
                        drop=True
                    )

                print(df.head())

                errors = custom_validate_df(
                    df, cmte_id, transaction_included, file_name
                )

                data = {
                    "error_list": errors.get("error_list"),
                    "fileName": file_name,
                    "duplicate_file_count": errors.get("duplcate_file_count"),
                    "duplicate_db_count": errors.get("duplicate_db_count"),
                }

                return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)

        except Exception as e:
            json_result = {"message": str(e)}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )

    except Exception as e:
        delete_import(cmte_id, file_name)
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


def create_entity_db_model(contacts_final_dict):
    if contacts_final_dict is None:
        return []
    try:
        all_contact = []
        with connection.cursor() as cursor:
            all_contact = [
                {
                    **contact,
                    "entity_id": get_next_entity_id(contact["entity_type"]),
                }
                for contact in contacts_final_dict
            ]

            psycopg2.extras.execute_batch(
                cursor,
                """
                INSERT INTO public.entity (
                    entity_id, cmte_id, entity_type, entity_name, first_name, last_name,
                    middle_name, preffix, suffix, street_1, street_2, city, state, zip_code,
                    occupation, employer
                )
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
                    %(employer)s
                );
                """,
                all_contact,
            )
        cursor.close()
        return all_contact

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts to database.")


def add_contact(cmte_id, file_name):
    contact_temp_list = get_temp_contact_list(cmte_id, file_name)
    contact_list = create_entity_db_model(contact_temp_list)
    return contact_list


@api_view(["POST"])
def ignore_merge(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == "POST":
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")
                transaction_included = request.data.get("transaction_included")
                if not check_null_value(file_name):
                    msg = "FileName cannot be null. Please pass file Name."
                    json_result = {"message": msg}
                    return JsonResponse(
                        json_result, status=status.HTTP_403_FORBIDDEN, safe=False
                    )

                contacts_added = add_contact(cmte_id, file_name)

                # create temp table for import transaction
                if transaction_included:
                    table_name = create_temp_contact_table(file_name)
                    create_temp_transaction_association_model(
                        contacts_added, table_name
                    )

                    # #code to read json file on aws
                    # object = client.get_object(Bucket = bucket, Key = uploaded_file_name)
                    # serialized_obj = object['Body'].read()
                    # myData = json.loads(serialized_obj)
                    # print(myData)

                contacts_deleted_size = delete_import(cmte_id, file_name)
                if contacts_deleted_size > 0:
                    logger.debug(
                        "Successfully clean contact temp table for committee {} and file {}".format(
                            cmte_id, file_name
                        )
                    )

                data = {
                    "message": "{} records were successfully added to database.".format(
                        len(contacts_added)
                    )
                }
                return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)

        except Exception as e:
            json_result = {"message": str(e)}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


def delete_import(cmte_id, file_name):
    try:
        with connection.cursor() as cursor:
            _sql = """DELETE FROM public.entity_import_temp
                        WHERE cmte_id = %s AND file_name = %s
                    """
            _v = (cmte_id, file_name)
            cursor.execute(_sql, _v)

        return cursor.rowcount
    except Exception as e:
        logger.debug("exception occurred while cancelling import contact", str(e))


@api_view(["POST"])
def cancel_import(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == "POST":
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")
                if not check_null_value(file_name):
                    msg = "FileName cannot be null. Please pass file Name."
                    json_result = {"message": msg}
                    return JsonResponse(
                        json_result, status=status.HTTP_403_FORBIDDEN, safe=False
                    )

                contacts_deleted_size = delete_import(cmte_id, file_name)
                data = {"message": "Successfully cancelled the import."}

                return JsonResponse(data, status=status.HTTP_204_NO_CONTENT, safe=False)

        except Exception as e:
            json_result = {"message": str(e)}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


def get_user_selected_option(contact):
    user_selection = ""
    if contact["file_selected"] is not None and check_null_value(
        contact["file_selected"]
    ):
        user_selection = "add"
    elif contact["update_db"] is not None and check_null_value(contact["update_db"]):
        user_selection = "update"
    elif contact["exsisting_db"] is not None and check_null_value(
        contact["exsisting_db"]
    ):
        user_selection = "exsisting"

    return user_selection


def get_user_selected_val(contact):
    user_selected_val = ""
    if contact["file_selected"] is not None and check_null_value(
        contact["file_selected"]
    ):
        user_selected_val = contact["file_selected"]
    elif contact["update_db"] is not None and check_null_value(contact["update_db"]):
        user_selected_val = contact["update_db"]
    elif contact["exsisting_db"] is not None and check_null_value(
        contact["exsisting_db"]
    ):
        user_selected_val = contact["exsisting_db"]

    return user_selected_val


def get_contacts_from_db(cmte_id, file_contact):
    db_contacts = get_list_contact(
        cmte_id, list(file_contact["duplicate_entity"].split(","))
    )

    for db_contact in db_contacts:
        if (
            db_contact["entity_id"] == file_contact["update_db"]
            or db_contact["entity_id"] == file_contact["exsisting_db"]
        ):
            db_contact["user_selected_value"] = True
        else:
            db_contact["user_selected_value"] = False
    return db_contacts


@api_view(["POST"])
def get_duplicate_contact(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == "POST":
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")
                page_num = int(request.data.get("page", 1))
                itemsperpage = request.data.get("itemsPerPage", 4)
                if not check_null_value(file_name):
                    msg = "FileName cannot be null. Please pass file Name."
                    json_result = {"message": msg}
                    return JsonResponse(
                        json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
                    )

                temp_list = get_temp_contact_pagination_list(
                    cmte_id, file_name, page_num, itemsperpage
                )

                all_contact = [
                    {
                        **contact,
                        "contact_from": "file",
                        "contacts_from_db": get_contacts_from_db(cmte_id, contact),
                        "user_selected_option": get_user_selected_option(contact),
                        "user_selected_value": get_user_selected_val(contact),
                    }
                    for contact in temp_list
                ]

                total_count = get_total_count(cmte_id, file_name)
                numofpages = get_num_of_pages(int(total_count), int(itemsperpage))
                all_done = check_if_all_options_selected(cmte_id, file_name)

                response = {
                    "contacts": list(all_contact),
                    "allDone": all_done,
                    "totalcontactsCount": total_count,
                    "itemsPerPage": itemsperpage,
                    "pageNumber": page_num,
                    "totalPages": int(numofpages),
                }

                return JsonResponse(
                    response, status=status.HTTP_201_CREATED, safe=False
                )

        except Exception as e:
            json_result = {"message": str(e)}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)
