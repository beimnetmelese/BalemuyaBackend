from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, ServiceCategoryViewSet, ServiceReviewViewSet, MyServicesViewSet

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'reviews', ServiceReviewViewSet)
router.register(r'myservices', MyServicesViewSet, basename='myservices')
router.register(r'', ServiceViewSet)



urlpatterns = router.urls
