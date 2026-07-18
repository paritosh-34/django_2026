import uuid

from django.db import models

from core.models import TimestampedModel
from orders.models import Order


# Create your models here.
class Payment(TimestampedModel):
    """tracks payment details against the order"""

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField(help_text="Amount in paise (500 rupees = 50000)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    # Razorpay references - this links our payment to razorpay records
    razorpay_payment_link_id = models.CharField(max_length=255, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    failure_reason_code = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Payment {self.payment_id} | Rs. {self.amount // 100} | {self.status}"


class WebhookEvent(TimestampedModel):
    """tracks webhook events"""
    event_id = models.CharField(max_length=255, unique=True, primary_key=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_id} ({self.event_type})"

