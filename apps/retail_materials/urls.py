
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.MaterialCategoryViewSet, basename='material-category')
router.register(r'materials', views.MaterialViewSet, basename='material')
router.register(r'components', views.ComponentViewSet, basename='component')
router.register(r'estimates', views.RetailEstimateViewSet, basename='retail-estimate')

urlpatterns = [
    path('', include(router.urls)),
]