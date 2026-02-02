# config/yourapp/views_admin_dashboard.py
from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User  # adjust paths as needed
from bookings.models import Transaction, Booking  # adjust paths as needed

PLATFORM_FEE_RATE = Decimal("0.10")  # 10% platform cut


def parse_period(request):
    """
    Accepts optional ?from=YYYY-MM-DD&to=YYYY-MM-DD
    Defaults: last 30 days [to=now, from=now-30d]
    """
    to_param = request.query_params.get("to")
    from_param = request.query_params.get("from")

    now = timezone.now()
    if to_param:
        try:
            to_dt = timezone.make_aware(timezone.datetime.fromisoformat(to_param) + timedelta(days=1))
        except Exception:
            to_dt = now
    else:
        to_dt = now

    if from_param:
        try:
            frm_dt = timezone.make_aware(timezone.datetime.fromisoformat(from_param))
        except Exception:
            frm_dt = to_dt - timedelta(days=30)
    else:
        frm_dt = to_dt - timedelta(days=30)

    if frm_dt > to_dt:
        frm_dt, to_dt = to_dt - timedelta(days=30), to_dt
    return frm_dt, to_dt


class AdminDashboardViewSet(viewsets.ViewSet):
    """
    Admin-only analytics for the platform.
    """
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        High-level summary for a period (transaction-based + bookings + users).
        """
        date_from, date_to = parse_period(request)

        # Transactions
        tx_qs = Transaction.objects.filter(created_at__range=(date_from, date_to))
        gross_revenue = tx_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        platform_profit = (gross_revenue * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
        providers_take = (gross_revenue - platform_profit).quantize(Decimal("0.01"))

        # Bookings
        bookings_qs = Booking.objects.filter(created_at__range=(date_from, date_to))
        booking_status_counts = bookings_qs.values("status").annotate(count=Count("id"))

        # Users
        new_users_count = User.objects.filter(joined_at__range=(date_from, date_to)).count()
        total_users_count = User.objects.count()

        return Response({
            "range": {"from": date_from, "to": date_to},
            "transactions": {
                "gross_revenue": str(gross_revenue),
                "platform_profit": str(platform_profit),
                "providers_take": str(providers_take),
                "count": tx_qs.count(),
            },
            "bookings": {
                "total": bookings_qs.count(),
                "status_counts": {b["status"]: b["count"] for b in booking_status_counts}
            },
            "users": {
                "new_users": new_users_count,
                "total_users": total_users_count
            }
        })

    @action(detail=False, methods=["get"])
    def timeseries(self, request):
        """
        Time-series revenue/profit over a period.
        ?granularity=day|week|month
        """
        date_from, date_to = parse_period(request)
        granularity = request.query_params.get("granularity", "day").lower()

        trunc = TruncDay
        if granularity == "week":
            trunc = TruncWeek
        elif granularity == "month":
            trunc = TruncMonth

        tx_qs = Transaction.objects.filter(
            created_at__range=(date_from, date_to)
            
        )

        series = (
            tx_qs
            .annotate(bucket=trunc("created_at"))
            .values("bucket")
            .annotate(gross=Sum("amount"))
            .order_by("bucket")
        )

        results = []
        for row in series:
            gross = row["gross"] or Decimal("0")
            profit = (gross * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
            take = (gross - profit).quantize(Decimal("0.01"))
            results.append({
                "bucket": row["bucket"],
                "gross": str(gross),
                "platform_profit": str(profit),
                "providers_take": str(take),
            })

        return Response({
            "range": {"from": date_from, "to": date_to},
            "granularity": granularity,
            "series": results,
        })

    @action(detail=False, methods=["get"])
    def top(self, request):
        """
        Top providers/services by revenue (from transactions).
        ?by=providers|services&limit=5
        """
        date_from, date_to = parse_period(request)
        limit = int(request.query_params.get("limit", 5))
        by = request.query_params.get("by", "providers")

        tx_qs = Transaction.objects.filter(
            created_at__range=(date_from, date_to)
            
        )

        if by == "services":
            data = (
                tx_qs
                .values("service_id", "service__title")
                .annotate(total=Sum("amount"), count=Count("id"))
                .order_by("-total")[:limit]
            )
            items = [{
                "service_id": r["service_id"],
                "service_title": r["service__title"],
                "revenue": str(r["total"] or 0),
                "transactions": r["count"],
            } for r in data]
        else:  # default providers
            data = (
                tx_qs
                .values("provider_id", "provider__full_name")
                .annotate(total=Sum("amount"), count=Count("id"))
                .order_by("-total")[:limit]
            )
            items = [{
                "provider_id": r["provider_id"],
                "provider_name": r["provider__full_name"],
                "revenue": str(r["total"] or 0),
                "transactions": r["count"],
            } for r in data]

        return Response({
            "range": {"from": date_from, "to": date_to},
            "by": by,
            "items": items,
        })
