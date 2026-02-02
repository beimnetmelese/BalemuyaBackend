from django.db import models
from django.utils import timezone
from accounts.models import User


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.customer} → {self.service} ({self.status})"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user} Wallet"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='booking')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_booking')
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # For payment gateway tracking

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.wallet.user})"
