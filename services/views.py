from rest_framework import viewsets, filters
from .models import Service, ServiceCategory, ServiceReview
from .serializers import ServiceSerializer, ServiceCategorySerializer, ServiceReviewSerializer
from groq import Groq
from dotenv import load_dotenv
import os
import json
from rapidfuzz import fuzz
from django.db.models import Q, Case, When
from django.db import models
from rest_framework.exceptions import ValidationError
from accounts.models import User
from django.shortcuts import get_object_or_404
from rest_framework.response import Response


def classify_query_categories(search_query: str, possible_categories: list[str]) -> list[str]:
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = (
        f"You are an expert classifier. Given the user search query: \"{search_query}\", "
        f"choose which of the following service categories it belongs to: {', '.join(possible_categories)}. "
        "You are an API. Only respond with a valid JSON array of category names that best match the following service search query.No extra text. No explanations. Example: ['Tutoring', 'Education']."
        "If the query does not match any category, return an empty array."
        )
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You classify user queries into service categories."},
            {"role": "user", "content": prompt},
        ],
        model="llama-3.3-70b-versatile",  # or use 'compound-beta' for built-in web search support :contentReference[oaicite:1]{index=1}
    )

    ai_response = response.choices[0].message.content
    
    raw = ai_response.strip()

    # First, try parsing normally
    try:
        categories = json.loads(raw)
        # If it's a string that contains JSON, parse again
        if isinstance(categories, str):
            categories = json.loads(categories)
    except json.JSONDecodeError:
        categories = []

    # Ensure it's a list of strings
    if not isinstance(categories, list):
        categories = []

    print("AI classified categories:", categories)
    return categories


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    queryset = Service.objects.all().select_related('category', 'provider')
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'category__name', 'provider__full_name']

    def perform_create(self, serializer):
        # Get telegram_id from query param or request data
        telegram_id = self.request.data.get('provider')
        if not telegram_id:
            raise ValidationError({"telegram_id": "Telegram ID is required."})

        provider = User.objects.filter(telegram_id=telegram_id).first()
        if not provider:
            raise ValidationError({"provider": "No provider found for this Telegram ID."})

        service = serializer.save(provider=provider)

        # Send Telegram message to provider after successful service registration
        from accounts.send_booking_message import send_booking_message
        send_booking_message(
            telegram_id=provider.telegram_id,
            message=f"Your service '{service.title}' has been registered successfully!",
            button_text="Go to Provider Dashboard",
            button_url="https://balemuya-frontend-qn6y.vercel.app/provider-dashboard"
        )

    def get_queryset(self):
        base_qs = self.queryset
        query = self.request.query_params.get('search', "").strip()

        if not query:
            return base_qs

        # 2️⃣ Fuzzy match on titles
        scored_services = []
        for service in base_qs:
            score = fuzz.WRatio(query.lower(), service.title.lower())
            print(score)
            if score >= 60:  # tweak threshold if needed
                scored_services.append((service.id, score))

        if scored_services:
            scored_services.sort(key=lambda x: x[1], reverse=True)
            ids_ordered = [sid for sid, _ in scored_services]
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(ids_ordered)],
                output_field=models.IntegerField()
            )
            return base_qs.filter(id__in=ids_ordered).order_by(preserved_order)
        
        # 1️⃣ Try AI category classification
        possible_categories = list(Service.objects.values_list('category__name', flat=True).distinct())
        ai_categories = classify_query_categories(query, possible_categories)

        if ai_categories:
            return base_qs.filter(category__name__in=ai_categories)

        # 3️⃣ Fallback: partial match on other fields
        return base_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(provider__full_name__icontains=query)
        )

    def filter_queryset(self, queryset):
        if self.request.query_params.get('search', None):
            return queryset
        return super().filter_queryset(queryset)

class ServiceReviewViewSet(viewsets.ModelViewSet):
    queryset = ServiceReview.objects.all().order_by('-created_at')
    serializer_class = ServiceReviewSerializer

    def create(self, request, *args, **kwargs):
        service_id = request.data.get('service')
        reviewer_id = request.data.get('reviewer')
        if service_id and reviewer_id:
            existing = ServiceReview.objects.filter(service_id=service_id, reviewer_id=reviewer_id).first()
            if existing:
                serializer = self.get_serializer(existing, data=request.data, partial=True)
                if not serializer.is_valid():
                    print("[ServiceReviewViewSet] Validation errors (update):", serializer.errors)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=200)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("[ServiceReviewViewSet] Validation errors (create):", serializer.errors)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
    
class MyServicesViewSet(viewsets.ModelViewSet):
    """
    Retrieve, update (partial or full) services for a specific provider
    """
    serializer_class = ServiceSerializer
    lookup_field = "id"
    queryset = Service.objects.all()

    def get_queryset(self):
        # Expect telegram_id as a query param
        telegram_id = self.request.query_params.get("telegram_id")
        if not telegram_id:
            return Service.objects.none()
        user = get_object_or_404(User, telegram_id=telegram_id)
        return Service.objects.filter(provider=user)

    def partial_update(self, request, *args, **kwargs):
        service = self.get_object()
        serializer = self.get_serializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Full update
        service = self.get_object()
        serializer = self.get_serializer(service, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)