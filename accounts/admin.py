
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("telegram_id", "username", "full_name", "phone_number", "role", "joined_at")
	search_fields = ("telegram_id", "username", "full_name", "phone_number")
	list_filter = ("role", "joined_at")

# Register your models here.
