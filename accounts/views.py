from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Business
from .utils import generate_business_code
from django.core.exceptions import ValidationError
# ========== ایمپورت‌های جدید برای DRF و JWT ==========
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, BusinessSerializer
# ====================================================
# ========== ویوهای قبلی تو ==========
@csrf_exempt
def signup_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        data = json.loads(request.body)
        recovery_contact = data.get("recovery_contact")
        password = data.get("password")
    except:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if not recovery_contact or not password:
        return JsonResponse({"error": "Missing fields."}, status=400)
    if Business.objects.filter(recovery_contact=recovery_contact).exists():
        return JsonResponse({"error": "This contact is already registered."}, status=400)
    try:
        code = generate_business_code()
        business = Business.objects.create_user(business_code=code, recovery_contact=recovery_contact, password=password)
        return JsonResponse({"success": True, "business_code": code})
    except ValidationError as e:
        return JsonResponse({"error": e.message_dict}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        data = json.loads(request.body)
        business_code = data.get("business_code")
        password = data.get("password")
    except:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if not business_code or not password:
        return JsonResponse({"error": "Missing fields."}, status=400)
    try:
        business = Business.objects.get(business_code=business_code)
    except Business.DoesNotExist:
        return JsonResponse({"error": "Business code not found."}, status=404)
    if business.status != "active":
        return JsonResponse({"error": "Business is suspended."}, status=403)
    if not business.check_password(password):
        return JsonResponse({"error": "Incorrect password."}, status=403)
    request.session["business_id"] = business.id
    return JsonResponse({"success": True, "business_code": business.business_code})

@csrf_exempt
def reset_password_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        data = json.loads(request.body)
        business_code = data.get("business_code")
        new_password = data.get("new_password")
    except:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if not business_code or not new_password:
        return JsonResponse({"error": "Missing fields."}, status=400)
    try:
        business = Business.objects.get(business_code=business_code)
        business.set_password(new_password)
        business.save()
        return JsonResponse({"success": True})
    except Business.DoesNotExist:
        return JsonResponse({"error": "Business code not found."}, status=404)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def recover_business_code_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        data = json.loads(request.body)
        recovery_contact = data.get("recovery_contact")
    except:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if not recovery_contact:
        return JsonResponse({"error": "Missing contact."}, status=400)
    businesses = Business.objects.filter(recovery_contact=recovery_contact)
    if not businesses.exists():
        return JsonResponse({"error": "No businesses found with this contact."}, status=404)
    codes = [b.business_code for b in businesses]
    return JsonResponse({"business_codes": codes})

# ======================================
# ========== ویوهای جدید JWT ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login_view(request):
    """ورود با JWT برای استفاده در DRF"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        business = serializer.validated_data['business']
       
        # ساخت JWT token
        refresh = RefreshToken.for_user(business)
       
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'business': BusinessSerializer(business).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh_view(request):
    """تازه‌سازی توکن"""
    from rest_framework_simplejwt.views import TokenRefreshView
    return TokenRefreshView.as_view()(request)
# ======================================