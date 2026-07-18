from django.urls import path
from . import views

urlpatterns = [
    path('create-link/', views.create_payment_link, name='create-payment-link'),
    path('callback/', views.payment_callback, name='payment-callback'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay-webhook'),
]