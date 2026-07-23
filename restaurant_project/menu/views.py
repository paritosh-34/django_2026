from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

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
            search_fields = ['^name', '=category__name', 'description']
            ordering_fields = ['name', 'price', 'created_at']   # whitelist
            ordering = ['name']

    SearchFilter prefixes (a char in front of the field changes the match):
        'name'    (none)  ->  icontains   LIKE '%foo%'   substring, anywhere
        '^name'   starts  ->  istartswith LIKE 'foo%'    prefix match
        '=name'   exact   ->  iexact      = 'foo'         whole-value match
        '@name'   full-text search (Postgres only)
        '$name'   regex

    Why the prefix matters — INDEXES:
        '%foo%' (default contains) has a leading wildcard, so the DB can't use a
        B-tree index — it scans every row. '^name' -> 'foo%' is anchored at the
        start, so an index on name CAN be used (huge win on big tables). '=' is
        an equality match, the most index-friendly of all. Rule of thumb: anchor
        the search (^ or =) when the column is indexed and the table is large;
        plain contains is fine for small tables. (Caveat: case-insensitive
        matching can still defeat the index unless you index lower(name) too.)

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

    # cache_page is a function-view decorator; method_decorator adapts it to a
    # class method. Keys on the FULL URL (incl. ?search / ?ordering / ?page), so
    # each filter combo caches separately. APIView's list handler is get() — a
    # ViewSet would decorate list() instead. Only GET/HEAD are cached; post()
    # is untouched. Trap: no auto-invalidation — a new item won't appear here
    # until the 5-min TTL expires. Fine for a public menu; wrong for per-user data.
    @method_decorator(cache_page(60 * 5))  # 5 minutes
    def get(self, request):
        items = MenuItem.objects.select_related('category')

        category = request.query_params.get('category')
        if category:
            items = items.filter(category__name__iexact=category)

        search = request.query_params.get('search')
        if search:
            # By hand, the SearchFilter prefixes map to ORM lookups:
            #   default '%foo%'  -> __icontains   (used here; not indexable)
            #   '^' prefix match -> __istartswith 'foo%'  (can use an index)
            #   '=' exact match  -> __iexact
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