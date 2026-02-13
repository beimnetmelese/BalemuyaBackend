
from django.contrib import admin
from .models import User
from .models_telegram_user import TelegramUser

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("telegram_id", "username", "full_name", "phone_number", "role", "joined_at")
	search_fields = ("telegram_id", "username", "full_name", "phone_number")
	list_filter = ("role", "joined_at")

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
	list_display = ("telegram_id", "started_at")
	search_fields = ("telegram_id",)
