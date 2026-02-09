from django.urls import path

# Import from views_enhanced.py (the new endpoints)
from apps.estimates.views_enhanced import (
    estimate_detailed,
    regenerate_detailed_estimate,
    estimate_by_category,
    download_estimate_excel,
    dxf_analysis_info
)

# Import from the main views.py (if you have these functions there)
# If these don't exist in views.py, comment them out or remove them
from apps.estimates.views import (
    project_estimate_summary,
    download_estimate_pdf,
)

urlpatterns = [
    # Original endpoints (from views.py)
    path(
        "projects/<int:project_id>/estimate/",
        project_estimate_summary,
        name="project-estimate-summary"
    ),
    path(
        "projects/<int:project_id>/estimate/download-pdf/",
        download_estimate_pdf,
        name="download-estimate-pdf"
    ),
    
    # Enhanced endpoints (from views_enhanced.py)
    path(
        'projects/<int:project_id>/estimate-detailed/', 
        estimate_detailed,
        name="estimate-detailed"
    ),
    path(
        'projects/<int:project_id>/regenerate-estimate/', 
        regenerate_detailed_estimate,
        name="regenerate-estimate"
    ),
    path(
        'projects/<int:project_id>/estimate-by-category/', 
        estimate_by_category,
        name="estimate-by-category"
    ),
    path(
        'projects/<int:project_id>/estimate/download-excel/', 
        download_estimate_excel,
        name="download-estimate-excel"
    ),
    path(
        'projects/<int:project_id>/dxf-analysis/', 
        dxf_analysis_info,
        name="dxf-analysis"
    ),
]