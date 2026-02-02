from django.contrib import admin
from .models import Service
from .models import ServiceCategory, ServiceReview

class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'price', 'available', 'created_at']
    readonly_fields = ['created_at']

admin.site.register(Service, ServiceAdmin)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    
@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin): 
    list_display = ['service', 'reviewer', 'rating', 'created_at']
    search_fields = ['service__title', 'reviewer__username']
    list_filter = ['rating', 'created_at']
    ordering = ['-created_at']