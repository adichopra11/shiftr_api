from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import ProfileView, RegisterView, VerifyEmail, LoginAPIView, GoogleSocialAuthView, DashboardView

urlpatterns = [
    path('profile', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name=''),
    path('google-auth/', GoogleSocialAuthView.as_view(), name='verify'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'), 
]
