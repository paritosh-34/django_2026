from django.db import models
import uuid

from core.models import TimestampedModel

# orders/models.py
class OrderQuerySet(models.QuerySet):
    """Custom QuerySet methods for Order."""
    def with_items(self):
        """Solve N+1 for items"""
        return self.prefetch_related('items__menu_item')

    def pending(self):
        return self.filter(status='pending')

    def active(self):
        """Orders that aren't cancelled or delivered."""
        return self.exclude(status__in=['cancelled', 'delivered'])

    def today(self):
        from django.utils import timezone
        return self.filter(created_at__date=timezone.now().date())

    def high_value(self, min_amount=100):
        return self.filter(total_amount__gte=min_amount)

    def needs_attention(self):
        """Pending orders older than 30 minutes."""
        from datetime import timedelta
        from django.utils import timezone
        threshold = timezone.now() - timedelta(minutes=30)
        return self.filter(status='pending', created_at__lte=threshold)

    # --- USAGE ---
    # # Clean, readable, DRY code!
    # Order.objects.pending()
    # Order.objects.active().today()
    # Order.objects.pending().high_value(min_amount=500)
    #
    # # Chain with regular filters
    # Order.objects.pending().filter(customer_name__icontains='john')

class Order(TimestampedModel):
    """A customer's order"""

    # This is how uuid is used
    # id = models.UUIDField(
    #     primary_key=True,
    #     default=uuid.uuid4,
    #     editable=False
    # )

    # DUAL ID approach
    # Internal integer ID (auto-generated, used for JOINs)
    id = models.BigAutoField(primary_key=True)

    # External UUID (exposed in API)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True  # Required for API lookups!
    )

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
    objects = OrderQuerySet.as_manager()

    # Many-to-Many with Through Model
    menu_items = models.ManyToManyField(
        'menu.MenuItem',
        through='OrderItem',
        related_name='orders'
    )

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

class OrderInvoice(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice'  # order.invoice
    )

# Many-to-Many with Through Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

# on_delete     Options
#
# Option	    Behavior
# CASCADE	    Delete children when parent deleted
# PROTECT	    Prevent deletion if children exist
# SET_NULL	    Set FK to NULL (requires null=True)
# SET_DEFAULT	Set FK to default value