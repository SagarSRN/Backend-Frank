from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import PlanUpload
from .serializers import PlanUploadSerializer
from .tasks import process_dxf_upload


class PlanUploadViewSet(viewsets.ModelViewSet):
    queryset = PlanUpload.objects.all()
    serializer_class = PlanUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        print("📦 REQUEST DATA:", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.save()

        # Detect file type
        filename = upload.file.name.lower()
        if filename.endswith(".dxf"):
            upload.file_type = "dxf"
        elif filename.endswith(".dwg"):
            upload.file_type = "dwg"
        else:
            upload.file_type = "unknown"

        upload.save()

        # ✅ RUN DIRECTLY (NO CELERY)
        if upload.file_type in ["dxf", "dwg"]:
            print("🚀 Running DXF processing synchronously")
            process_dxf_upload(upload.id)

        return Response(
            {
                "message": "Plan uploaded and processed",
                "project_id": upload.project.id,
                "upload_id": upload.id,
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET"])
def project_upload_status(request, project_id):
    upload = (
        PlanUpload.objects.filter(project_id=project_id)
        .order_by("-uploaded_at")
        .first()
    )

    if not upload:
        return Response({"status": "no_upload"})

    return Response(
        {
            "status": "completed" if upload.processed else "processing"
        }
    )
