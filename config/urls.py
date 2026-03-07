from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.uploads.urls")),      # Upload endpoints
    path("api/", include("apps.estimates.urls")),    # Estimate endpoints
    path("api/", include("apps.projects.urls")),
    path('api/retail/', include('apps.retail_materials.urls')),# Project endpoints
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)