from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AdminDashboardViewSet

router = DefaultRouter()
router.register(r'', AdminDashboardViewSet, basename='admin-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]