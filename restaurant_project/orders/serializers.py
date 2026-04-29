from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'customer_name', 'customer_phone', 'customer_email', 'status', 'total_amount')

    def validate_customer_phone(self, value):
        """Phone must be at least 10 digits."""
        # Remove any non-digit characters for validation
        digits_only = ''.join(filter(str.isdigit, value))
        if len(digits_only) < 10:
            raise serializers.ValidationError(
                "Phone number must have at least 10 digits"
            )
        return value