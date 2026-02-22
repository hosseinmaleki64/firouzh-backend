from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('recover-business-code/', views.recover_business_code_view, name='recover_business_code'),
    path('jwt/login/', views.jwt_login_view, name='jwt_login'),
    path('jwt/refresh/', views.jwt_refresh_view, name='jwt_refresh'),
]