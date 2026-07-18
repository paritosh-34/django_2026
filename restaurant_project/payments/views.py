import json
import razorpay
from django.db import transaction

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order
from payments.models import Payment, WebhookEvent
from restaurant_project import settings

# Create your views here.
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@require_POST
def create_payment_link(request):
    """
    Creates a Razorpay Payment Link for an order.
    The link is sent to the customer via SMS/email by Razorpay itself.
    """
    data = json.loads(request.body)
    order_id = data.get('order_id')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # Calculate amount in paise
    amount_paise = int(order.calculate_total() * 100)

    # Create Payment record in our DB
    payment = Payment.objects.create(
        order=order,
        amount=amount_paise,
        status=Payment.Status.CREATED,
    )

    # Create Razorpay Payment Link
    link_data = client.payment_link.create({
        'amount': amount_paise,
        'currency': 'INR',
        'description': f'Payment for Order #{order.id}',
        'customer': {
            'name': order.customer_name,
            'email': order.customer_email,
            'contact': order.mobile_number or '9999999999',
        },
        'notify': {
            'sms': True,
            'email': True,
        },
        'notes': {
            'order_id': str(order.id),
            'payment_uuid': str(payment.payment_id),
        },
        'callback_url': f'{settings.BASE_URL}/payments/callback/',
        'callback_method': 'get',
    })

    # Save Razorpay Payment Link ID
    payment.razorpay_payment_link_id = link_data['id']
    payment.save()

    return JsonResponse({
        'payment_link_id': link_data['id'],
        'payment_link_url': link_data['short_url'],
        'amount': amount_paise,
        'our_payment_id': str(payment.payment_id),
        'status': 'created',
    })

@csrf_exempt
def payment_callback(request):
    """
    Razorpay redirects the customer here after payment.
    This is just for UX — NOT the source of truth.
    The webhook is the source of truth.
    """
    razorpay_payment_id = request.GET.get('razorpay_payment_id', '')
    razorpay_payment_link_id = request.GET.get('razorpay_payment_link_id', '')

    return JsonResponse({
        'message': 'Payment callback received',
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_payment_link_id': razorpay_payment_link_id,
        'note': 'This is just for UX. Webhook is the source of truth.',
    })

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Razorpay calls this when payment status changes.
    THIS is the source of truth for updating payment status.
    """
    payload = request.body
    signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

    # 1. Verify signature — ensures the request is actually from Razorpay
    try:
        client.utility.verify_webhook_signature(
            payload.decode('utf-8'),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        return HttpResponse('Invalid signature', status=400)

    event = json.loads(payload)

    # 2. Idempotency — skip if we already processed this event
    event_id = event.get('event_id', '')
    if WebhookEvent.objects.filter(event_id=event_id).exists():
        return HttpResponse('Already processed', status=200)

    # 3. Process inside a database transaction (all-or-nothing)
    try:
        with transaction.atomic():
            event_type = event.get('event', '')

            if event_type == 'payment_link.paid':
                _handle_payment_link_paid(event)
            elif event_type == 'payment.failed':
                _handle_payment_failed(event)

            # Record the event so we don't process it again
            WebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                payload=event,
                processed=True,
            )

        return HttpResponse('OK', status=200)

    except Exception as e:
        # Return 500 so Razorpay retries later
        return HttpResponse(f'Error: {e}', status=500)


def _handle_payment_link_paid(event):
    """Payment link was paid — update our records."""
    payment_link = event['payload']['payment_link']['entity']
    payment_entity = event['payload']['payment']['entity']
    link_id = payment_link.get('id', '')

    try:
        payment = Payment.objects.get(razorpay_payment_link_id=link_id)
        payment.status = Payment.Status.PAID
        payment.razorpay_payment_id = payment_entity.get('id', '')
        payment.save()

        # Update order status
        payment.order.status = Order.Status.CONFIRMED
        payment.order.save()
    except Payment.DoesNotExist:
        pass

def _handle_payment_failed(event):
    """Payment failed."""
    payment_entity = event['payload']['payment']['entity']
    notes = payment_entity.get('notes', {})
    payment_uuid = notes.get('payment_uuid', '')

    try:
        payment = Payment.objects.get(payment_id=payment_uuid)
        payment.status = Payment.Status.FAILED
        payment.failure_reason = payment_entity.get('error_description', 'Unknown')
        payment.save()
    except Payment.DoesNotExist:
        pass
