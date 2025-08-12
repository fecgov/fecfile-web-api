from datetime import datetime
import math
from .models import Imports, ImportStatus
from fecfiler.committee_accounts.models import CommitteeAccount
from .serializers import ImportsSerializer
from django.core.files.storage import FileSystemStorage
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.web_services.importing.dotfec_preprocess import DotFEC_Preprocessor
from fecfiler.web_services.importing.dotfec_import import DotFEC_Importer

class ImportsListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class ImportsViewSet(ModelViewSet):
    def get_queryset(self):
        return super().get_queryset()

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Imports.objects.all()

    serializer_class = ImportsSerializer
    pagination_class = ImportsListPagination

    @action(detail=False, methods=["post"])
    def upload_dotfec(self, request):
        if "dotfec" in request.FILES:
            fs = FileSystemStorage()
            uploaded_file = request.FILES["dotfec"]
            committee_id = request.session.get("committee_id", None)
            committee_uuid = request.session.get("committee_uuid", None)
            if committee_id is not None and committee_uuid is not None:
                committee_account = CommitteeAccount.objects.get(id=committee_uuid)
                timestamp = math.floor(datetime.now().timestamp())
                filename = f"uploads/{committee_id}_import_{timestamp}.fec"

                new_import = Imports()
                new_import.dot_fec_file = filename
                new_import.status = ImportStatus.UPLOADING.value
                new_import.committee_account = committee_account
                new_import.save()

                try:
                    fs.save(filename, uploaded_file)
                except Exception:
                    new_import.status = ImportStatus.FAILED_UPLOAD.value
                    new_import.save()
                    return Response(ImportsSerializer(new_import).data, status=422)

                new_import.status = ImportStatus.PREPROCESSING.value
                new_import.save()

                DotFEC_Preprocessor(new_import)

                new_import.refresh_from_db()
                return Response(ImportsSerializer(new_import).data, status=200)
        return Response(status=400)

    @action(detail=False, methods=["post"])
    def approve_for_import(self, request):
        import_id = request.data.get("id", None)
        if import_id is None:
            return Response("id is a required parameter", status=400)

        import_obj = Imports.objects.filter(id=import_id).first()
        if import_obj is None:
            return Response("id did not match any known import objects", status=400)
        
        updated_json = request.data.get("updated_json", None)
        if updated_json:
            try:
                import_obj.preprocessed_json = updated_json
                import_obj.save()
            except Exception:
                return Response("failed to update json", status=422)

        try:
            DotFEC_Importer(import_obj)
        except Exception:
            import_obj.refresh_from_db()
            return Response(ImportsSerializer(import_obj).data, status=422)

        import_obj.refresh_from_db()
        return Response(ImportsSerializer(import_obj).data, status=200)


