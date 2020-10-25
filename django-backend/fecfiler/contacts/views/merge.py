import datetime
import logging

import psycopg2
from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view

from fecfiler.authentication.authorization import is_read_only_or_filer_reports
from fecfiler.core.views import get_comittee_id, check_null_value, get_list_contact, NoOPError, get_next_entity_id

logger = logging.getLogger(__name__)


def update_user_selection(entity_id, user_selected_val, option_selected, cmte_id):
    if option_selected == "add":
        selected_field_val = "file_selected"
        other_option_1 = "update_db"
        other_option_2 = "exsisting_db"
    elif option_selected == "update":
        selected_field_val = "update_db"
        other_option_1 = "file_selected"
        other_option_2 = "exsisting_db"
    elif option_selected == "exsisting":
        selected_field_val = "exsisting_db"
        other_option_1 = "update_db"
        other_option_2 = "file_selected"

    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.entity_import_temp SET """ + selected_field_val + """= %s, """ + other_option_1 + """ = %s, """ + \
                   other_option_2 + """ = %s WHERE entity_id = %s AND cmte_id = %s"""
            _v = (
                user_selected_val,
                "",
                "",
                entity_id,
                cmte_id
            )
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.debug("Updating user info for {} failed."
                             " No record was found")
        return cursor.rowcount
    except Exception as e:
        logger.debug("Exception occurred while updating user", str(e))
        raise e


def check_if_all_options_selected(cmte_id, file_name):
    try:
        all_selected = False
        with connection.cursor() as cursor:
            query_string = """SELECT count(*) FROM public.entity_import_temp WHERE cmte_id = %s AND file_name = %s AND duplicate_entity NOT IN ('', ' ') and
             file_selected in ('', ' ') and (update_db <> '') is not true and (exsisting_db <> '') is not true"""

            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, file_name])
            row1 = cursor.fetchone()[0]
            list(row1)
            totalcount = row1[0]['count']
            if totalcount == 0:
                all_selected = True

        return all_selected
    except Exception as e:
        raise e

def check_temp_contact_list_done(cmte_id, file_name):
    try:
        sql_count = """
            select count(1) as count_not_done
            from public.entity_import_temp 
            where cmte_id = %(cmte_id)s and file_name = %(file_name)s
            and length(file_selected) = 0
        """
        sql = """SELECT json_agg(t) FROM (""" + sql_count + """) t"""
        with connection.cursor() as cursor:
            cursor.execute(sql, {
                "cmte_id": cmte_id,
                "file_name": file_name   
            })
            row1=cursor.fetchone()[0]
            totalcount =  row1[0]['count_not_done']

        if totalcount > 0:
            return False

        return True
    except Exception as e:
        raise e

@api_view(["POST"])
def merge_option(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == 'POST':
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")
                merge_parameters = request.data.get("merge_option")
                user_option = merge_parameters['user_selected_option']
                file_entity_id = int(merge_parameters['file_record_id'])
                db_entity_id = merge_parameters['db_entity_id']

                sql = """
                    UPDATE public.entity_import_temp 
                    SET file_selected = %(user_option)s
                        ,update_db = %(db_entity_id)s
                    WHERE entity_id = %(file_entity_id)s AND cmte_id = %(cmte_id)s 
                """
                with connection.cursor() as cursor:
                    cursor.execute(sql, {
                        "cmte_id": cmte_id,
                        "file_entity_id": file_entity_id,
                        "user_option": user_option,
                        "db_entity_id": db_entity_id   
                    })
                    if cursor.rowcount != 1:
                        logger.debug("Updating user info for {} failed."
                                    " No record was found")

                # add_list = []
                # update_list = []
                # exsist_list = []
                # if not check_null_value(file_name) and len(options_list) == 0:
                #     msg = "FileName or option list cannot be null. Please pass file Name and option list."
                #     json_result = {'message': msg}
                #     return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

                # for option in options_list:
                #     if option["selected"].lower() == "add":
                #         add_list.append(option["entity_id"])
                #         update_user_selection(option["entity_id"], "true", "add", cmte_id)
                #     elif option["selected"].lower() == "update":
                #         update_list.append(
                #             {
                #                 "entity_id": option["entity_id"],
                #                 "update_id": option["val"]
                #             }
                #         )
                #         update_user_selection(option["entity_id"], option["val"], "update", cmte_id)
                #     elif option["selected"].lower() == "exsisting":
                #         exsist_list.append(
                #             {
                #                 "entity_id": option["entity_id"],
                #                 "ignore_id": option["val"]
                #             }
                #         )
                #         update_user_selection(option["entity_id"], option["val"], "exsisting", cmte_id)

                # all_selected = check_if_all_options_selected(cmte_id, file_name)
                all_done = check_temp_contact_list_done(cmte_id, file_name)

                return JsonResponse({'msg': 'Success', 'all_selected': True, 'allDone': all_done }, status=status.HTTP_200_OK,
                                    safe=False)

        except Exception as e:
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


def get_add_contact(cmte_id, file_name):
    try:
        with connection.cursor() as cursor:
            query_string = """SELECT entity_id, cmte_id, transaction_id, file_name, entity_type, street_1, street_2, city, state, zip_code,employer,occupation,entity_name,last_name,first_name, middle_name, preffix, suffix
                                                FROM public.entity_import_temp WHERE cmte_id = %s AND file_name = %s AND file_selected = %s"""
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, file_name, "true"])
            contact_list = cursor.fetchall()
            if not contact_list:
                return None
            merged_list = []
            for dictL in contact_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        raise e


def get_update_contact(cmte_id, file_name, choice):
    if choice == "update":
        field = "update_db"
    elif choice == "exsisting":
        field = "exsisting_db"
    try:
        with connection.cursor() as cursor:
            query_string = """SELECT entity_id, cmte_id, transaction_id, file_name, entity_type, street_1, street_2, city, state, """ + field + """, zip_code,employer,occupation,entity_name,last_name,first_name, middle_name, preffix, suffix
                                                FROM public.entity_import_temp WHERE cmte_id = %s AND file_name = %s AND """ + field + """ not in ('', ' ')"""
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, file_name])
            contact_list = cursor.fetchall()
            if not contact_list:
                return None
            merged_list = []
            for dictL in contact_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        raise e


def create_entity_update_db_model(contacts_final_dict):
    try:
        for contact in contacts_final_dict:
            print(contact)
        all_contact = []
        with connection.cursor() as cursor:
            all_contact = [{
                **contact,
                "last_update_date": datetime.datetime.now(),
            } for contact in contacts_final_dict]

            psycopg2.extras.execute_batch(cursor, """
                        UPDATE public.entity SET entity_type = %(entity_type)s, entity_name = %(entity_name)s, first_name = %(first_name)s, last_name = %(last_name)s, middle_name = %(middle_name)s, preffix = %(preffix)s,
                         suffix = %(suffix)s, street_1 = %(street_1)s, street_2 = %(street_2)s, city = %(city)s, state = %(state)s, zip_code = %(zip_code)s,
                          occupation = %(occupation)s, employer = %(employer)s, last_update_date = %(last_update_date)s where cmte_id = %(cmte_id)s AND entity_id = %(update_db)s;
                    """, all_contact)
        cursor.close()
        return all_contact

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while updating bulk contacts to database.", e)

def create_entity_db_model(contacts_final_dict):
    try:
        for contact in contacts_final_dict:
            print(contact)
        all_contact = []
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
        return all_contact

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts to database.")


def create_entity_log_model(old_update_list, username):
    try:
        for contact in old_update_list:
            print(contact)
        all_contact = []
        with connection.cursor() as cursor:
            all_contact = [{
                **contact,
                "last_update_date": datetime.datetime.now(),
                "username": username
            } for contact in old_update_list]

            psycopg2.extras.execute_batch(cursor, """
                        INSERT INTO public.entity_log (entity_id, cmte_id, entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1,
                         street_2, city, state, zip_code, occupation, employer, last_update_date, logged_date, username) VALUES (
                            %(entity_id)s,
                            %(cmte_id)s,
                            %(entity_type)s,
                            %(entity_name)s,
                            %(first_name)s,
                            %(last_name)s,
                            %(middle_name)s,
                            %(prefix)s,
                            %(suffix)s,
                            %(street_1)s,
                            %(street_2)s,
                            %(city)s,
                            %(state)s,
                            %(zip_code)s,
                            %(occupation)s,
                            %(employer)s,
                            %(last_update_date)s,
                            %(last_update_date)s,
                            %(username)s
                        );
                    """, all_contact)
        cursor.close()
        return all_contact

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts history log to database.", e)


def create_temp_contact_table(file_name):
    table_name = "contacts_" + file_name
    index = table_name.rfind(".")
    table_name = table_name[:index]
    print(table_name)

    try:
        with connection.cursor() as cursor:
            query_string = """CREATE TABLE IF NOT EXISTS public.""" +table_name+"""(cmte_id character varying(9) NOT NULL,file_name character varying(200) NOT NULL,entity_id varchar(30) NOT NULL,transaction_id character varying(200) NOT NULL)"""
            cursor.execute(query_string)

        return table_name
    except Exception as e:
        raise e


def create_temp_transaction_association_model(total_list, table_name):
    try:
        for contact in total_list:
            print(contact)
        all_contact = []
        with connection.cursor() as cursor:
            all_contact = [{
                **contact,
                "table_name": table_name
            } for contact in total_list]

            psycopg2.extras.execute_batch(cursor, """
                        INSERT INTO public.""" + table_name + """ (entity_id, cmte_id, transaction_id, file_name) VALUES (
                            %(entity_id)s,
                            %(cmte_id)s,
                            %(transaction_id)s,
                            %(file_name)s                           
                        );
                    """, all_contact)
        cursor.close()
        return all_contact

    except Exception as e:
        logger.debug(e)
        raise NoOPError("Error occurred while saving bulk contacts history log to database.", e)


@api_view(["POST"])
def merge_contact(request):
    try:
        is_read_only_or_filer_reports(request)
        try:
            if request.method == 'POST':
                cmte_id = get_comittee_id(request.user.username)
                file_name = request.data.get("fileName")
                transaction_included = request.data.get("transaction_included")
                username = request.user.username
                add_list = []
                update_list = []
                exsist_list = []
                total_list = []
                old_update_entity_list = []
                old_update_list = []
                old_exsist_entity_list = []
                contact_added_list = []
                contact_updated_list = []

                add_list = get_add_contact(cmte_id, file_name)
                update_list = get_update_contact(cmte_id, file_name, "update")
                exsist_list = get_update_contact(cmte_id, file_name, "exsisting")

                if add_list is not None and len(add_list) > 0:
                    contact_added_list = create_entity_db_model(add_list)
                if update_list is not None and len(update_list) > 0:
                    for update_contact in update_list:
                        old_update_entity_list.append(update_contact["update_db"])

                    old_update_list = get_list_contact(cmte_id, old_update_entity_list)
                    contact_updated_list = create_entity_update_db_model(update_list)
                    # update entity log to persist entity history
                    create_entity_log_model(old_update_list, username)

                if exsist_list is not None and len(exsist_list) > 0 and transaction_included:

                    for exsist_contact in exsist_list:
                        old_exsist_entity_list.append({"entity_id": exsist_contact["exsisting_db"],
                                                       "transaction_id": exsist_contact["transaction_id"], "file_name": exsist_contact["file_name"],
                                                       "cmte_id": cmte_id})

                if transaction_included:
                    contact_new_update_list = []
                    for contact in contact_updated_list:
                        contact_new_update_list.append({"entity_id": contact["update_db"],
                                                       "transaction_id": contact["transaction_id"], "file_name": contact["file_name"],
                                                       "cmte_id": cmte_id})
                    total_list.extend(contact_added_list)
                    total_list.extend(contact_new_update_list)
                    total_list.extend(old_exsist_entity_list)
                    table_name = create_temp_contact_table(file_name)

                    create_temp_transaction_association_model(total_list, table_name)

                # Delete records from temp table - uncomment after test
                contacts_deleted_size = delete_import(cmte_id, file_name)
                if contacts_deleted_size > 0:
                    logger.debug("Successfully clean contact temp table for committee {} and file {}", cmte_id,
                                 file_name)

                return JsonResponse({'msg': 'Successfully Merged Contacts'}, status=status.HTTP_201_CREATED, safe=False)

        except Exception as e:
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

    except Exception as e:
        json_result = {'message': str(e)}
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
