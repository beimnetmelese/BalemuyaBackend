from rest_framework import serializers
from .models_telegram_user import TelegramUser

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = '__all__'
