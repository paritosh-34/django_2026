from django.db import models

from core.models import TimestampedModel

# Create your models here.
class Order(TimestampedModel):
    """A customer's order"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.status})"

class RecentOrder(Order):
    """Orders from the last 7 days - for dashboard."""
    class Meta:
        proxy = True
        ordering = ['-created_at']

    @classmethod
    def get_queryset(cls):
        from datetime import timedelta
        from django.utils import timezone
        week_ago = timezone.now() - timedelta(days=7)
        return cls.objects.filter(created_at__gte=week_ago)

class ArchivedOrder(Order):
    """Orders older than 30 days - for reports."""
    class Meta:
        proxy = True

    @classmethod
    def get_queryset(cls):
        from datetime import timedelta
        from django.utils import timezone
        month_ago = timezone.now() - timedelta(days=30)
        return cls.objects.filter(created_at__lt=month_ago)
