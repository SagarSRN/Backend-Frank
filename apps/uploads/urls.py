
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PlanUploadViewSet, project_upload_status

router = DefaultRouter()
router.register(r"uploads", PlanUploadViewSet, basename="uploads")

urlpatterns = router.urls + [
    path(
        "projects/<int:project_id>/upload-status/",
        project_upload_status,
        name="project-upload-status",
    ),
]
