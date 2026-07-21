from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.menu_list, name='menu_list'),
    # path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('item/<str:item_id>/', views.item_detail, name='item_detail'),

    # DRF API — class-based views need .as_view()
    path('items/', views.MenuItemListView.as_view(), name='api_menu_items'),
    path('items/<uuid:item_id>/', views.MenuItemDetailView.as_view(), name='api_menu_item_detail'),
]


