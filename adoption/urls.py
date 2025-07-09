from django.urls import path
from .views import (
    RegisterView, AnimalListCreateView, AnimalDetailView,
    AppointmentListCreateView, AppointmentDetailView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('animals/', AnimalListCreateView.as_view(), name='animal-list-create'),
    path('animals/<int:pk>/', AnimalDetailView.as_view(), name='animal-detail'),

    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
]
