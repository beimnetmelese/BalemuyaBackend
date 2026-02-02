from rest_framework import serializers
from .models import Service, ServiceCategory, ServiceReview

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class ServiceReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)

    class Meta:
        model = ServiceReview
        fields = '__all__'

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ServiceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews = ServiceReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ["provider"]
