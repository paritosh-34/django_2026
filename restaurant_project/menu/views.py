from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
# menu/views.py

def home(request):
    """
    The simplest possible view.
    - Receives: HttpRequest object
    - Returns: HttpResponse object
    """
    return HttpResponse("Welcome to our restaurant! 🍽️")


def menu_list(request):
    """A view that returns a simple menu."""
    menu_items = """
    <h1>Today's Menu</h1>
    <ul>
        <li>Pasta Carbonara - $15</li>
        <li>Grilled Salmon - $22</li>
        <li>Caesar Salad - $12</li>
    </ul>
    """
    return HttpResponse(menu_items)

# URL: /menu/item/42/
def item_detail(request, item_id):  # item_id is passed automatically!
    # item_id = 42 (as an integer, not string)
    return HttpResponse(f"Showing item #{item_id}")