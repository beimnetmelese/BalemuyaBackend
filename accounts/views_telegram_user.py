from rest_framework import viewsets
from .models_telegram_user import TelegramUser
from .serializers_telegram_user import TelegramUserSerializer
from rest_framework.response import Response

class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    lookup_field = 'telegram_id'

    def create(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({'detail': 'telegram_id is required'}, status=400)
        obj, created = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=201 if created else 200)
