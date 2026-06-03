from django.contrib import admin

from orders.models import RecentOrder, ArchivedOrder


# Register your models here.
@admin.register(RecentOrder)
class RecentOrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'status', 'created_at']

@admin.register(ArchivedOrder)
class ArchivedOrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'status', 'created_at']