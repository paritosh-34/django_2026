from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.menu_list, name='menu_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
]


