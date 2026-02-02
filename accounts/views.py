from rest_framework import viewsets
from .models import User
from accounts import send_booking_message
from .serializers import UserSerializer
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'telegram_id'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("[User Registration Error]", serializer.errors)
            # If telegram_id already exists, treat as success and return the existing user
            if 'telegram_id' in serializer.errors:
                error_msgs = serializer.errors['telegram_id']
                if any('already exists' in str(msg) for msg in error_msgs):
                    telegram_id = request.data.get('telegram_id')
                    user = User.objects.filter(telegram_id=telegram_id).first()
                    if user:
                        return Response(self.get_serializer(user).data, status=200)
            return Response(serializer.errors, status=400)
        user = serializer.save()
        # Send Telegram message after registration
        send_booking_message(
            telegram_id=user.telegram_id,
            message="Registration successful! Welcome to Balemuya.",
            button_text="Go to Dashboard",
            button_url="https://balemuya-frontend-qn6y.vercel.app/"
        )
        return Response(self.get_serializer(user).data, status=201)
