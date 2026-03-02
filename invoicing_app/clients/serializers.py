from rest_framework import serializers
from invoicing_app.clients.models import Client, ClientAddress, ClientContact
from invoicing_app.core.validators import ClientValidationMixin, NestedValidationMixin, ValidationMixin


class ClientAddressSerializer(serializers.ModelSerializer):
    """
    Nested serializer for client addresses.
    """
    class Meta:
        model = ClientAddress
        fields = [
            'id', 'address_type', 'street_1', 'street_2', 'city', 'state_province', 
            'postal_code', 'country', 'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientContactSerializer(serializers.ModelSerializer):
    """
    Nested serializer for client contacts.
    """
    class Meta:
        model = ClientContact
        fields = [
            'id', 'name', 'title', 'email', 'phone', 'is_primary', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientSerializer(ClientValidationMixin, NestedValidationMixin, ValidationMixin, serializers.ModelSerializer):
    """
    Client serializer with nested addresses and contacts support.
    Handles complex nested creates and updates with comprehensive validation.
    """
    addresses = ClientAddressSerializer(many=True, required=False, read_only=False)
    contacts = ClientContactSerializer(many=True, required=False, read_only=False)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Client
        fields = [
            'id', 'uuid', 'name', 'client_type', 'business_registration_number', 'tax_id', 
            'email', 'phone', 'currency', 'default_tax_rate', 'payment_terms_days', 
            'credit_limit', 'addresses', 'contacts', 'created_by', 'created_by_email',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Create client with nested addresses and contacts.
        """
        addresses_data = validated_data.pop('addresses', [])
        contacts_data = validated_data.pop('contacts', [])
        
        client = Client.objects.create(**validated_data)
        
        # Create addresses
        for addr_data in addresses_data:
            ClientAddress.objects.create(client=client, **addr_data)
        
        # Create contacts
        for contact_data in contacts_data:
            ClientContact.objects.create(client=client, **contact_data)
        
        return client

    def update(self, instance, validated_data):
        """
        Update client with nested addresses and contacts.
        """
        addresses_data = validated_data.pop('addresses', None)
        contacts_data = validated_data.pop('contacts', None)
        
        # Update client fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        
        # Update addresses (clear and recreate)
        if addresses_data is not None:
            instance.addresses.all().delete()
            for addr_data in addresses_data:
                ClientAddress.objects.create(client=instance, **addr_data)
        
        # Update contacts (clear and recreate)  
        if contacts_data is not None:
            instance.contacts.all().delete()
            for contact_data in contacts_data:
                ClientContact.objects.create(client=instance, **contact_data)
        
        return instance

    def validate_tax_id(self, value):
        """
        Validate tax ID format.
        Kenya PIN: 8-10 digits or format like A001234567X
        """
        if not value:
            return value
        
        # Remove common separators
        cleaned = value.replace('-', '').replace(' ', '').upper()
        
        # Check format: Either all digits (PIN) or alphanumeric (VAT)
        if not (cleaned.isdigit() or cleaned.isalnum()):
            raise serializers.ValidationError(
                "Tax ID must contain only alphanumeric characters (e.g., A001234567X)."
            )
        
        if len(cleaned) < 8:
            raise serializers.ValidationError(
                "Tax ID must be at least 8 characters long."
            )
        
        return value

    def validate_currency(self, value):
        """
        Validate currency code (Kenya support with USD/EUR options).
        """
        valid_currencies = ['KES', 'USD', 'EUR']
        if value and value not in valid_currencies:
            raise serializers.ValidationError(
                f"Currency must be one of {', '.join(valid_currencies)}."
            )
        return value

    def validate_payment_terms_days(self, value):
        """
        Validate payment terms are non-negative.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Payment terms must be a non-negative number of days."
            )
        return value

    def validate_credit_limit(self, value):
        """
        Validate credit limit is non-negative.
        """
        self.validate_non_negative_decimal(value, 'Credit limit')
        return value
