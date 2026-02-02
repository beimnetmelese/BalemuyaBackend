from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views_telegram_user import TelegramUserViewSet

router = DefaultRouter()
router.register(r'telegram-users', TelegramUserViewSet)
router.register(r'', UserViewSet)
urlpatterns = router.urls
