from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except Exception:
            raise serializers.ValidationError(
                {"error": "Invalid username or password"}
            )

        user = self.user

        data["user_id"] = user.id
        data["username"] = user.username

        group = user.groups.first()
        data["role"] = group.name if group else "employee"

        return data
