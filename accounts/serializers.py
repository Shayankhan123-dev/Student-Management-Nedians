from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        # authenticate() checks username+password against the database
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError('Invalid username or password.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been disabled.')

        # attach the user object so the view can access it
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes user data for responses.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'full_name', 'is_active']

    def get_full_name(self, obj):
        """
        Try to get full_name from student profile.
        If user is admin, fall back to username.
        """
        try:
            return obj.student_profile.full_name
        except Exception:
            return obj.get_full_name() or obj.username