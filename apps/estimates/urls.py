from django.urls import path
from apps.estimates.views import (
    GenerateEstimateAPIView,
    project_estimate_summary,
)

urlpatterns = [
    path(
        "projects/<int:project_id>/generate-estimate/",
        GenerateEstimateAPIView.as_view()
    ),
    path(
        "projects/<int:project_id>/estimate/",
        project_estimate_summary
    ),
]
