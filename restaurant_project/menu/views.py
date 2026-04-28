from django.shortcuts import render
from django.http import HttpResponse

from .models import MenuItem


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
    # """A view that returns a simple menu."""
    # menu_items = """
    # <h1>Today's Menu</h1>
    # <ul>
    #     <li>Pasta Carbonara - $15</li>
    #     <li>Grilled Salmon - $22</li>
    #     <li>Caesar Salad - $12</li>
    # </ul>
    # """
    # return HttpResponse(menu_items)
    # items = MenuItem.objects.all()
    items = MenuItem.objects.filter(is_available=True)

    response = "<h3>My menu items are:</h3>"
    response += "\n<ul>"
    for item in items:
        response += f"\n<li>{item.name}</li>"

    response += "\n</ul>"

    return HttpResponse(response)



# URL: /menu/item/42/
def item_detail(request, item_id):  # item_id is passed automatically!
    # item_id = 42 (as an integer, not string)
    return HttpResponse(f"Showing item #{item_id}")