"""
Serializers for accounts & auth workflows.
"""

from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, trim_whitespace=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=6)

class SendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

class UpdateProfileSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
