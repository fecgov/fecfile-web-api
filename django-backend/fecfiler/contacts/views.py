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
from fecfiler.core.views import get_comittee_id, NoOPError, get_next_entity_id

logger = logging.getLogger(__name__)


def schema_validation(uploaded_df):
    try:
        schema = Schema([
            Column('COMMITTEE_ID', [MatchesPatternValidation('[cC][0-9]{8}')]),
            Column('ENTITY_TYPE', [InListValidation(['IND', 'ORG'])]),
            Column('STREET_1', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,34}$')]),
            Column('STREET_2', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,34}$')]),
            Column('CITY', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,30}$')]),
            Column('STATE', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{2}$')]),
            Column('ZIP', [MatchesPatternValidation('^[\\w\\s]{1,9}$')]),
            Column('EMPLOYER', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,38}$')]),
            Column('OCCUPATION', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,38}$')]),
            Column('ORGANIZATION_NAME', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,200}$')]),
            Column('LASTNAME', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,30}$')]),
            Column('FIRSTNAME', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,20}$')]),
            Column('MIDDLENAME', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,20}$')]),
            Column('PREFIX', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,10}$')]),
            Column('SUFFIX', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,10}$')])
        ])

        errors = schema.validate(uploaded_df)

        errors_index_rows = [e.row for e in errors]
        data_clean = uploaded_df.drop(index=errors_index_rows)
        data_dirty = pd.concat([data_clean, uploaded_df]).drop_duplicates(keep=False)
        data = {"errors": data_dirty, "data_clean": data_clean}
        return data
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while validating file structure. Please ensure header and data values are in "
                        "proper format.")


def custom_validate_df(uploaded_df_orig, cmte_id):
    try:

        uploaded_df_orig.ZIP = uploaded_df_orig.ZIP.astype(str)

        uploaded_df = uploaded_df_orig.drop_duplicates()

        uploaded_df_duplicates = uploaded_df_orig[uploaded_df_orig.duplicated(keep=False)]
        uploaded_df_duplicates = uploaded_df_duplicates.drop_duplicates()

        uploaded_df_cmt = uploaded_df[uploaded_df.COMMITTEE_ID.str.contains(cmte_id, case=False)]
        uploaded_df_cmt_error = pd.concat([uploaded_df, uploaded_df_cmt]).drop_duplicates(keep=False)

        schema_data = schema_validation(uploaded_df_cmt)
        errors = schema_data.get("errors")
        data_clean = schema_data.get("data_clean")

        data_clean = data_clean.replace(r'^\s+$', np.nan, regex=True)

        # this will drop all rows with misiing or nan values
        test_data_temp = data_clean.dropna(how='any',
                                           subset=['COMMITTEE_ID', 'ENTITY_TYPE', 'STREET_1', 'CITY', 'STATE', 'ZIP'])

        test_data_diff = pd.concat([test_data_temp, data_clean]).drop_duplicates(keep=False)

        test_data_ind = test_data_temp.ENTITY_TYPE.str.contains('IND', case=False)
        test_data_ind1 = test_data_temp[test_data_ind]

        if not test_data_ind1.empty:
            test_data_ind_temp = test_data_ind1.dropna(how='any',
                                                       subset=['LASTNAME', 'FIRSTNAME'])

        test_data_ind_diff = pd.concat([test_data_ind1, test_data_ind_temp]).drop_duplicates(keep=False)

        test_data_org = test_data_temp.ENTITY_TYPE.str.contains('ORG', case=False)
        test_data_org1 = test_data_temp[test_data_org]

        if not test_data_org1.empty:
            test_data_org_temp = test_data_org1.dropna(how='any',
                                                       subset=['ORGANIZATION_NAME'])

        test_data_org_diff = pd.concat([test_data_org1, test_data_org_temp]).drop_duplicates(keep=False)

        test_data_final = pd.concat([test_data_ind_temp, test_data_org_temp]).reset_index(drop=True)
        test_data_null_final = pd.concat([test_data_ind_diff, test_data_org_diff, test_data_diff,
                                          errors, uploaded_df_cmt_error]).reset_index(drop=True)

        data = {"final_list": test_data_final, "required_field_missing_list": test_data_null_final,
                "duplicates_files": uploaded_df_duplicates}

        return data

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while applying custom validation. Please ensure header and data values are in "
                        "proper format.")


def get_contact_list(cmte_id):
    try:
        with connection.cursor() as cursor:
            query_string = """SELECT cmte_id,entity_type,street_1, street_2, city, state, zip_code,employer,occupation,entity_name,last_name,first_name, middle_name, preffix, suffix
                                                FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y'"""
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id])
            contact_list = cursor.fetchall()
            if not contact_list:
                raise NoOPError("No entity found for cmte_id {} ".format(cmte_id))
            merged_list = []
            for dictL in contact_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        raise e


def reorder_user_data(contacts_added, contact_list):
    try:
        contacts_added.columns = ['cmte_id', 'entity_type', 'street_1', 'street_2', 'city', 'state', 'zip_code',
                                  'employer',
                                  'occupation', 'entity_name', 'last_name', 'first_name', 'middle_name', 'preffix',
                                  'suffix']
        print(type(contacts_added))
        contacts_list_dict = pd.DataFrame.from_records(contact_list)
        contacts_list_dict['street_1'] = contacts_list_dict['street_1'].str.strip()
        contacts_added.zip_code = contacts_added.zip_code.astype(str)
        contacts_added.reset_index(drop=True, inplace=True)

        json_added = contacts_added.to_json(orient='records')
        json_contact = contacts_list_dict.to_json(orient='records')
        contacts_added_dict = pd.read_json(json_added)
        contact_list_dict = pd.read_json(json_contact)
        contact_list_dict.fillna(value=pd.np.nan, inplace=True)
        contact_list_dict1 = contact_list_dict.replace(np.nan, '', regex=True)
        contacts_added_dict.zip_code = contacts_added_dict.zip_code.astype(str)
        contacts_added_dict1 = contacts_added_dict.replace(np.nan, '', regex=True)
        print(contacts_added_dict1.dtypes)
        print(contact_list_dict.dtypes)

        contact_final_dict = contacts_added_dict1.merge(contact_list_dict1, how='outer', indicator=True).loc[
            lambda x: x['_merge'] == 'left_only']

        contact_duplicate_dict = contacts_added_dict1.merge(contact_list_dict1, how='inner', indicator=False)
        print(type(contact_duplicate_dict))
        del contact_final_dict['_merge']
        data = {"final_contact_df": contact_final_dict, "duplicate_contact_df": contact_duplicate_dict}
        return data
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Exception occurred while reformatting the data.")


def create_db_model(contacts_final_dict):
    try:
        contacts_final_dict = contacts_final_dict.to_dict(orient='records')
        for contact in contacts_final_dict:
            print(contact)
        with connection.cursor() as cursor:
            all_contact = [{
                **contact,
                'entity_id': get_next_entity_id(contact['entity_type']),
            } for contact in contacts_final_dict]

            psycopg2.extras.execute_batch(cursor, """
                        INSERT INTO public.entity (entity_id, cmte_id, entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer) VALUES (
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
                    """, all_contact)

        cursor.close()
    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts to database.")


def save_contact_db(contacts_added, cmte_id):
    contact_list = get_contact_list(cmte_id)
    data = reorder_user_data(contacts_added, contact_list)
    create_db_model(data.get("final_contact_df"))

    return data


@api_view(["POST"])
def upload_contact(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == 'POST':
                cmte_id = get_comittee_id(request.user.username)
                client = boto3.client('s3',
                                      settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
                                      )
                bucket = "fecfile-filing-frontend"
                file_name = request.data.get("fileName")
                csv_obj = client.get_object(Bucket=bucket, Key=file_name)
                body = csv_obj['Body']
                csv_string = body.read().decode('utf-8')

                df = pd.read_csv(StringIO(csv_string), dtype=object)

                print(df.head())

                data = custom_validate_df(df, cmte_id)

                contacts_added = data.get("final_list")

                contacts_null_value = data.get("required_field_missing_list").replace(np.nan, '', regex=True)
                contacts_null_dict = contacts_null_value.to_dict(orient='records')

                save_data = save_contact_db(contacts_added, cmte_id)
                final_contact_list = save_data.get("final_contact_df")
                final_contact_list_dict = final_contact_list.to_dict(orient='records')

                duplicates = pd.concat([data.get("duplicates_files"), save_data.get("duplicate_contact_df")]).reset_index(
                    drop=True).replace(np.nan, '', regex=True)
                duplicate_dict = duplicates.to_dict(orient='records')
                contacts_temp = {"contacts": final_contact_list_dict, "contacts_failed_validation": contacts_null_dict,
                                 "duplicate": duplicate_dict}
                contacts = {"Response": contacts_temp}

                return JsonResponse(contacts, status=status.HTTP_201_CREATED, safe=False)

        except Exception as e:
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

