from rest_framework import serializers
from .models import Booking, Wallet, Transaction
from services.serializers import ServiceSerializer
from accounts.serializers import UserSerializer  # or create a minimal user serializer

class BookingSerializer(serializers.ModelSerializer):
    # Nested serializers
    customer = UserSerializer(read_only=True)
    provider = UserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['provider', 'created_at']

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ['balance', 'user']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['created_at']

