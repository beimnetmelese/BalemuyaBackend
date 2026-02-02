from django.db import models

class User(models.Model):
    telegram_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=[('customer', 'Customer'), ('pro', 'Professional')],
        default='customer'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or self.username or self.telegram_id
