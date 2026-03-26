from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Organization, OrganizationMember, Subscription, Invoice


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class OrganizationSerializer(serializers.ModelSerializer):
    plan_limits = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'uuid', 'name', 'slug', 'description', 'website', 'logo',
            'plan', 'admin_email', 'phone', 'invoice_count', 'user_count',
            'status', 'stripe_customer_id', 'subscription_renew_date',
            'enable_api_access', 'enable_custom_branding', 'enable_advanced_analytics',
            'plan_limits', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'stripe_customer_id', 'invoke_count', 'created_at', 'updated_at']
    
    def get_plan_limits(self, obj):
        return obj.get_plan_limits()


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ['id', 'uuid', 'user', 'user_email', 'user_name', 'role', 'is_primary', 'joined_at']
        read_only_fields = ['uuid', 'joined_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'uuid', 'organization', 'organization_name', 'plan', 'status',
            'start_date', 'current_period_start', 'current_period_end', 'trial_end',
            'amount', 'currency', 'auto_renew', 'payment_method', 'is_active'
        ]
        read_only_fields = ['uuid', 'start_date']


class InvoiceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'uuid', 'invoice_number', 'organization', 'organization_name',
            'amount', 'tax', 'status', 'issue_date', 'due_date', 'paid_date',
            'description', 'stripe_invoice_id'
        ]
        read_only_fields = ['uuid', 'invoice_number', 'issue_date']
