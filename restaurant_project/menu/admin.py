from django.contrib import admin
from .models import Category, MenuItem
# Register your models here.

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name']
    list_editable = ['price', 'is_available']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = ['name']
    search_fields = ['name']
    list_editable = ['description']
