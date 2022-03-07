from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from fecfiler.core.views import get_comittee_id, get_list_contact


def get_entity_contact_list(cmte_id):
    try:
        with connection.cursor() as cursor:
            query_string = """
            SELECT cmte_id, entity_id, entity_type, entity_name, first_name, last_name,
            middle_name, preffix as prefix, suffix, street_1, street_2, city, state,
            zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district,
            ref_cand_cmte_id
            FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y'
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id]
            )
            contact_list = cursor.fetchall()

            merged_list = []
            for dictL in contact_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        raise e


@api_view(["POST"])
def contact_details(request):
    try:
        if request.method == "POST":
            cmte_id = get_comittee_id(request.user.username)
            send_all_flag = request.data.get("sendAll")
            entity_list = request.data.get("entity")

            if send_all_flag:
                contact_list = get_entity_contact_list(cmte_id)
                return JsonResponse(
                    {"contacts": list(contact_list)},
                    status=status.HTTP_200_OK,
                    safe=False,
                )
            elif len(entity_list) > 0:
                contact_list = get_list_contact(cmte_id, list(entity_list))
                return JsonResponse(
                    {"contacts": list(contact_list)},
                    status=status.HTTP_200_OK,
                    safe=False,
                )

            data = {"contact": []}

            return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)
