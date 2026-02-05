from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, project_summary

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")

urlpatterns = [
    path("", include(router.urls)),
    path("projects/<int:project_id>/summary/", project_summary),
]
