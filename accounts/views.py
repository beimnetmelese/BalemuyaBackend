from rest_framework import viewsets
from .models import User
from .send_booking_message import send_booking_message_sync
from .serializers import UserSerializer
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'telegram_id'

    def create(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user:
            # Update user with new info
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                return Response(self.get_serializer(user).data, status=200)
            else:
                print("[User Update Error]", serializer.errors)
                return Response(serializer.errors, status=400)
        # If not exists, create new
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("[User Registration Error]", serializer.errors)
            return Response(serializer.errors, status=400)
        user = serializer.save()
        # Send Telegram message after registration
        send_booking_message_sync(
            telegram_id=user.telegram_id,
            message="Registration successful! Welcome to Balemuya.",
            button_text="Go to Dashboard",
            button_url="https://balemuya-frontend-qn6y.vercel.app/"
        )
        return Response(self.get_serializer(user).data, status=201)
