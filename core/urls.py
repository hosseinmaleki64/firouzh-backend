from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
        path('', lambda r: HttpResponse("""
        <h1 style="text-align:center; margin-top:100px; font-family:Arial;">
            ✅ بک‌اند Django روی Render زنده است!<br><br>
            firouzh-backend.onrender.com<br>
            حالا می‌تونیم فرانت رو وصل کنیم 🚀
        </h1>
    """), name='home'),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/', include('products.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/orders/', include('orders.urls')),
    path('api/reports/', include('reports.urls')),
]