from django.urls import path
from apps.estimates.views import (
    GenerateEstimateAPIView,
    project_estimate_summary,
    download_estimate_pdf,
)

# Import enhanced views
from apps.estimates.views_enhanced import (
    estimate_detailed,
    regenerate_detailed_estimate,
    estimate_by_category,
    download_estimate_excel,
    dxf_analysis_info
)

urlpatterns = [
    # Original endpoints
    path(
        "projects/<int:project_id>/generate-estimate/",
        GenerateEstimateAPIView.as_view()
    ),
    path(
        "projects/<int:project_id>/estimate/",
        project_estimate_summary
    ),
    path(
        "projects/<int:project_id>/estimate/download-pdf/",
        download_estimate_pdf,
        name="download-estimate-pdf"
    ),
    
    # Enhanced endpoints
    path(
        'projects/<int:project_id>/estimate-detailed/', 
        estimate_detailed
    ),
    path(
        'projects/<int:project_id>/regenerate-estimate/', 
        regenerate_detailed_estimate
    ),
    path(
        'projects/<int:project_id>/estimate-by-category/', 
        estimate_by_category
    ),
    path(
        'projects/<int:project_id>/estimate/download-excel/', 
        download_estimate_excel
    ),
    path(
        'projects/<int:project_id>/dxf-analysis/', 
        dxf_analysis_info
    ),
]
