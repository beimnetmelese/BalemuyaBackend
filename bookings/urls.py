from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, WalletViewSet, TransactionViewSet, AdminDashboardAPIView,ProviderBookingViewSet
from django.urls import path

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'provider/bookings', ProviderBookingViewSet, basename='provider-bookings')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = router.urls + [
    path('admin/dashboard/', AdminDashboardAPIView.as_view(), name='admin-dashboard'),
]
