from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.CharField(max_length=64, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.telegram_id
