from rest_framework import serializers
from django.contrib.auth.models import User
from invoicing_app.user_management.models import UserRole, CustomUser


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for UserRole model with permission list.
    """
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description', 'permissions', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser profile extension.
    Includes basic Django User info (username, email, first_name, last_name).
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'uuid', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'is_active', 'is_staff', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'is_active', 'is_staff']

    def update(self, instance, validated_data):
        """
        Update CustomUser and linked Django User fields.
        """
        user_data = validated_data.pop('user', {})
        
        # Update Django User fields if provided
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        # Update CustomUser fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance
