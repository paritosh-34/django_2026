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
    GET  /menu/items/  — paginated, filterable, searchable, sortable list
    POST /menu/items/  — create an item

    Simpler alternative (the lecturer's version):

        class MenuItemListView(generics.ListAPIView):
            queryset = MenuItem.objects.select_related('category').all()
            serializer_class = MenuItemSerializer
            pagination_class = MenuPagination
            filter_backends = [filters.SearchFilter, filters.OrderingFilter]
            search_fields = ['name', 'description', 'category__name']
            ordering_fields = ['name', 'price', 'created_at']   # whitelist
            ordering = ['name']

    ~7 lines instead of ~30. We DIDN'T use it here on purpose, for two reasons:
      1. `menu` is our "APIView, full manual control" app — kept side by side
         with the generic style so the difference is visible.
      2. SearchFilter/OrderingFilter cover ?search= and ?ordering= for free,
         but NOT our custom ?category= and ?available= exact-match filters.
         Those need a 3rd backend (DjangoFilterBackend, `pip install
         django-filter`). Writing get() by hand keeps all four filters in one
         place with no extra dependency.

    Trap: filter_backends / search_fields / ordering_fields are read by
    GenericAPIView, NOT by APIView. Pasted onto this class they'd be silently
    ignored — no error, they just do nothing. The base class and the magic
    attributes are a package deal.
    """

    # Whitelist for ?ordering= — NEVER pass raw user input to order_by(). A
    # client could otherwise sort by any field/relation, or crash us on a typo.
    ORDERING_FIELDS = {'name', 'price', 'created_at'}
    DEFAULT_ORDERING = 'name'

    def get(self, request):
        items = MenuItem.objects.select_related('category')

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

        # Ordering last. A leading '-' means descending: ?ordering=-price.
        # order_by() is required anyway — LIMIT/OFFSET without ORDER BY lets the
        # DB return rows in any order, so items can repeat across pages.
        ordering = request.query_params.get('ordering', self.DEFAULT_ORDERING)
        if ordering.lstrip('-') in self.ORDERING_FIELDS:
            items = items.order_by(ordering)
        else:
            items = items.order_by(self.DEFAULT_ORDERING)  # ignore junk input

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