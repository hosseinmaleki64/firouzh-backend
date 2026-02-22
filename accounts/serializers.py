from rest_framework import serializers
from .models import Business

class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['id', 'business_code', 'recovery_contact', 'status', 'created_at']
        read_only_fields = ['business_code', 'created_at']

class LoginSerializer(serializers.Serializer):
    business_code = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            business = Business.objects.get(business_code=data['business_code'])
            if not business.check_password(data['password']):
                raise serializers.ValidationError("رمز عبور اشتباه است")
            if business.status != "active":
                raise serializers.ValidationError("حساب کاربری غیرفعال است")
        except Business.DoesNotExist:
            raise serializers.ValidationError("کد کسب و کار وجود ندارد")

        return {
            'business': business
        }