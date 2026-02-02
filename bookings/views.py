from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, Wallet, Transaction, User  # make sure you import User if needed
from .serializers import BookingSerializer, WalletSerializer, TransactionSerializer
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper, Q
from django.utils.timezone import now, timedelta
from rest_framework.views import APIView
from services.models import Service  # Assuming you have a Service model
from django.db.models import Case, When, Value, IntegerField, F, DateTimeField
from django.utils.timezone import now
from django.shortcuts import get_object_or_404


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    # No permission_classes needed if you want it open

    def get_queryset(self):
        qs = self.queryset

        if self.action == "list":
            telegram_id = self.request.query_params.get('telegram_id')
            if not telegram_id:
                return Booking.objects.none()
            qs = qs.filter(customer__telegram_id=telegram_id)

        # future first (0), past second (1)
        # then: within future -> scheduled_date ASC
        #       within past   -> scheduled_date DESC
        return (
            qs.annotate(
                is_future=Case(
                    When(scheduled_date__gte=now(), then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
                future_date=Case(  # only set for future items
                    When(scheduled_date__gte=now(), then=F('scheduled_date')),
                    default=Value(None),
                    output_field=DateTimeField(),
                ),
                past_date=Case(    # only set for past items
                    When(scheduled_date__lt=now(), then=F('scheduled_date')),
                    default=Value(None),
                    output_field=DateTimeField(),
                ),
            )
            .order_by('is_future', 'future_date', '-past_date')
        )
    
    def perform_create(self, serializer):
        telegram_id = self.request.query_params.get('telegram_id') or self.request.headers.get('telegram_id') or 123456
        if not telegram_id:
            return Response({"detail": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Assuming your User model stores telegram_id field
        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({"detail": "User with this telegram_id not found"}, status=status.HTTP_404_NOT_FOUND)
        service_id = self.request.data.get('service')
        service = Service.objects.filter(id=service_id).first()
        if not service:
            return Response({"detail": "Service not found"}, status=status.HTTP_404_NOT_FOUND)
        booking = serializer.save(customer=user, provider=service.provider, service=service)

        # Send Telegram message to client and provider
        from accounts.send_booking_message import send_booking_message
        # Client message
        send_booking_message(
            telegram_id=user.telegram_id,
            message=f"Your booking for {service.title} is created!",
            button_text="View Booking",
            button_url="https://balemuya-frontend-qn6y.vercel.app/bookings"
        )
        # Provider message
        send_booking_message(
            telegram_id=service.provider.telegram_id,
            message=f"New booking for your service: {service.title}",
            button_text="View Provider Dashboard",
            button_url="https://balemuya-frontend-qn6y.vercel.app/provider-dashboard"
        )

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    def get_queryset(self):
        telegram_id = self.request.query_params.get('telegram_id') or self.request.headers.get('telegram_id')
        if not telegram_id:
            return Wallet.objects.none()
        return Wallet.objects.filter(user__telegram_id=telegram_id)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        telegram_id = self.request.query_params.get('telegram_id') or self.request.headers.get('telegram_id')
        if not telegram_id:
            return Transaction.objects.none()
        return Transaction.objects.filter(wallet__user__telegram_id=telegram_id)

def get_dashboard_stats():
    today = now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    completed_qs = Booking.objects.filter(status='completed')

    def calculate_share(qs):
        return qs.aggregate(
            share=ExpressionWrapper(Sum(F('price') * 0.10), output_field=FloatField())
        )['share'] or 0

    total_earned_day = completed_qs.filter(scheduled_date__date=today).aggregate(total=Sum('price'))['total'] or 0
    total_earned_week = completed_qs.filter(scheduled_date__date__gte=week_start).aggregate(total=Sum('price'))['total'] or 0
    total_earned_month = completed_qs.filter(scheduled_date__date__gte=month_start).aggregate(total=Sum('price'))['total'] or 0
    total_earned_year = completed_qs.filter(scheduled_date__date__gte=year_start).aggregate(total=Sum('price'))['total'] or 0

    share_day = calculate_share(completed_qs.filter(scheduled_date__date=today))
    share_week = calculate_share(completed_qs.filter(scheduled_date__date__gte=week_start))
    share_month = calculate_share(completed_qs.filter(scheduled_date__date__gte=month_start))
    share_year = calculate_share(completed_qs.filter(scheduled_date__date__gte=year_start))

    completed_count = completed_qs.count()
    pending_count = Booking.objects.filter(status='pending').count()
    cancelled_count = Booking.objects.filter(status='cancelled').count()
    in_progress_count = Booking.objects.filter(status='in_progress').count()

    data = {
        "total_earned_day": total_earned_day,
        "total_earned_week": total_earned_week,
        "total_earned_month": total_earned_month,
        "total_earned_year": total_earned_year,

        "share_day": share_day,
        "share_week": share_week,
        "share_month": share_month,
        "share_year": share_year,

        "completed_bookings": completed_count,
        "pending_bookings": pending_count,
        "cancelled_bookings": cancelled_count,
        "in_progress_bookings": in_progress_count,
    }

    return data

class AdminDashboardAPIView(APIView):

    def get(self, request):
        data = get_dashboard_stats()
        return Response(data)

class ProviderBookingViewSet(viewsets.ModelViewSet):
    """
    Provider Dashboard: list bookings for their services and accept pending bookings
    """
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()

    def get_queryset(self):
        telegram_id = self.request.query_params.get("telegram_id")
        if not telegram_id:
            return Booking.objects.none()
        provider = get_object_or_404(User, telegram_id=telegram_id)
        qs = Booking.objects.filter(provider=provider)

        # annotate future/past for ordering
        return qs.annotate(
            is_future=Case(
                When(scheduled_date__gte=now(), then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            future_date=Case(
                When(scheduled_date__gte=now(), then=F('scheduled_date')),
                default=Value(None),
                output_field=DateTimeField()
            ),
            past_date=Case(
                When(scheduled_date__lt=now(), then=F('scheduled_date')),
                default=Value(None),
                output_field=DateTimeField()
            )
        ).order_by('is_future', 'future_date', '-past_date')

    def partial_update(self, request, *args, **kwargs):
        booking = self.get_object()
        new_status = request.data.get("status")

        if new_status == "in_progress":
            # Can only accept pending bookings
            if booking.status != "pending":
                return Response(
                    {"detail": "You can only accept pending bookings."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif new_status == "cancelled":
            # Can cancel only pending or in_progress bookings
            if booking.status not in ["pending", "in_progress"]:
                return Response(
                    {"detail": "You can only cancel pending or in-progress bookings."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "Invalid status change."},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = new_status
        booking.save()

        # Send Telegram message to client and provider on status change
        from accounts.send_booking_message import send_booking_message
        send_booking_message(
            telegram_id=booking.customer.telegram_id,
            message=f"Your booking for {booking.service.title} status changed to {booking.status}!",
            button_text="View Booking",
            button_url="https://balemuya-frontend-qn6y.vercel.app/bookings"
        )
        send_booking_message(
            telegram_id=booking.provider.telegram_id,
            message=f"Booking for your service {booking.service.title} status changed to {booking.status}!",
            button_text="View Provider Dashboard",
            button_url="https://balemuya-frontend-qn6y.vercel.app/provider-dashboard"
        )

        serializer = self.get_serializer(booking)
        return Response(serializer.data)