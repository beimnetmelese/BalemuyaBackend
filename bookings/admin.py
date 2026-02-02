from django.contrib import admin
from .models import Booking, Wallet, Transaction

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'customer', 'provider', 'status', 'scheduled_date', 'price', 'created_at')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('customer__username', 'provider__username', 'service__title')
    ordering = ('-created_at',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance')
    search_fields = ('user__username',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('wallet__user__username', 'description')
    ordering = ('-created_at',)
