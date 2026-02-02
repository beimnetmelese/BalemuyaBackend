from django.db import models
from accounts.models import User

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    provider = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="services"
    )
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255, blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)

    def average_rating(self):
        reviews = self.reviews.all()
        return reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0

    def __str__(self):
        return self.title


class ServiceReview(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_given"
    )
    rating = models.PositiveSmallIntegerField()  # 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service', 'reviewer')  # prevent multiple reviews per user

    def __str__(self):
        return f"{self.rating}★ - {self.service.title}"
