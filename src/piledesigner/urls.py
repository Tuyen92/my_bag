"""
URL configuration for piledesigner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from shared.views import DefaultViewSet
from users import views as userViews
from projects import views as projViews
from companies import views as comViews


router = routers.DefaultRouter()
router.register(r'', DefaultViewSet, basename='')
router.register(r'v1/user', userViews.UserViewSet)
router.register(r'v1/users/register', userViews.UserRegistrationViewSet, basename='register')
router.register(r'v1/auth/login', userViews.UserLoginViewSet, basename='login')
router.register(r'v1/auth', userViews.LogoutViewSet, basename='logout')

router.register(r'group', userViews.GroupViewSet)

router.register(r'v1/companies', comViews.CompanyViewSet, basename='company')
router.register(r'v1/companies/(?P<company_id>\d+)/projects', projViews.ProjectViewSet, basename='project')
router.register(r'v1/companies/(?P<company_id>\d+)/employees', userViews.UserViewSet, basename='employee')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),

    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', userViews.CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('api/token/check/', userViews.CheckTokenExpiryView.as_view(), name='check-token-expiry'),
    path('api/token/refresh/', userViews.CustomTokenRefreshView.as_view(), name='custom_token_refresh'),
    path('v1/otp/resend-otp/', userViews.ResendOTPView.as_view(), name='resend-otp'),
    path('v1/otp/verify-otp/', userViews.VerifyOTPView.as_view(), name='verify-otp'),
    path('v1/otp/reset-password/', userViews.ResetPassWithOTPView.as_view(), name='reset-password'),
]

# curl -X POST -H "Content-Type: application/json" -d '{"username": "admin", "password": "admin"}' http://localhost:8000/api/token/
