from rest_framework import serializers
from .models import Category, MenuItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class MenuItemSerializer(serializers.ModelSerializer):
    # Read-only extra field: follows the FK so the client gets the category
    # name without a second request. 'category' still takes an id on write.
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = (
            'id', 'name', 'description', 'price', 'is_available',
            'category', 'category_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_price(self, value):
        """Price must be positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value