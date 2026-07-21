from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem
from .serializers import MenuItemSerializer


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
        response += f"\n<li>{item.id} - {item.name}</li>"

    response += "\n</ul>"

    return HttpResponse(response)



# URL: /menu/item/42/
def item_detail(request, item_id):  # item_id is passed automatically!
    # item_id = 42 (as an integer, not string)
    # item = MenuItem.objects.filter(Q(name=item_id) | Q(id=item_id))
    try:
        item = MenuItem.objects.get(id=item_id)
    except MenuItem.DoesNotExist:
        return HttpResponse("ITEM NOT FOUND", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    else:
        return HttpResponse(f"Item {item_id} found!", status=200)
    # finally:
        # Do something after all of the above


# ---------------------------------------------------------------------------
# DRF API views
# ---------------------------------------------------------------------------

class MenuPagination(PageNumberPagination):
    page_size = 10                   # Default items per page
    page_size_query_param = 'size'   # Client can override: ?size=50
    max_page_size = 100              # Cap it — don't let client request 10,000


class MenuItemListView(APIView):
    """
    GET  /menu/api/items/  — paginated, filterable list
    POST /menu/api/items/  — create an item
    """

    def get(self, request):
        # order_by is required: LIMIT/OFFSET without ORDER BY lets the DB
        # return rows in any order, so items can repeat across pages.
        items = MenuItem.objects.select_related('category').order_by('name')

        category = request.query_params.get('category')
        if category:
            items = items.filter(category__name__iexact=category)

        search = request.query_params.get('search')
        if search:
            items = items.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        available = request.query_params.get('available')
        if available is not None:
            items = items.filter(is_available=available.lower() == 'true')

        # With APIView we drive the paginator ourselves. A generic view would
        # do these three lines for us.
        paginator = MenuPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        serializer = MenuItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = MenuItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 400 with field errors
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MenuItemDetailView(APIView):
    """GET / PUT / PATCH / DELETE a single item."""

    def get_object(self, item_id):
        return MenuItem.objects.select_related('category').filter(id=item_id).first()

    def get(self, request, item_id):
        item = self.get_object(item_id)
        if item is None:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MenuItemSerializer(item).data)

    def put(self, request, item_id):
        return self._update(request, item_id, partial=False)

    def patch(self, request, item_id):
        return self._update(request, item_id, partial=True)

    def _update(self, request, item_id, partial):
        item = self.get_object(item_id)
        if item is None:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MenuItemSerializer(item, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, item_id):
        item = self.get_object(item_id)
        if item is None:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)