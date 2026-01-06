from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Basic user info
        token["user_id"] = user.id
        token["username"] = user.username

        # SAFE group/role handling (NO IndexError)
        group = user.groups.first()
        token["role"] = group.name if group else "employee"

        return token
