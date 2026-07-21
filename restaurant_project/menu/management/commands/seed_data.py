"""
Seed the DB with realistic sample data.

Run it:
    python manage.py seed_data          # add sample data
    python manage.py seed_data --fresh   # wipe sample tables first, then add

Why a management command (vs a script you paste into `manage.py shell`)?
  - It lives in the repo and is rerunnable — like a `seed.js` wired into the CLI.
  - Django auto-discovers it from the folder path:
        menu/management/commands/seed_data.py  ->  `manage.py seed_data`
    The filename IS the command name. The two __init__.py files are what make
    Python treat the folders as packages so the discovery works.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from menu.models import Category, MenuItem, Food, Beverage
from orders.models import Order, OrderItem


CATEGORIES = {
    'Starters':        'Small plates to begin the meal',
    'Main Course':     'Hearty curries and mains',
    'Breads':          'Fresh from the tandoor',
    'Rice & Biryani':  'Rice dishes and biryanis',
    'Desserts':        'Something sweet to finish',
    'Beverages':       'Hot and cold drinks',
}

# (name, category, price, is_available)
MENU_ITEMS = [
    ('Paneer Tikka',           'Starters',       Decimal('280.00'), True),
    ('Chicken 65',             'Starters',       Decimal('320.00'), True),
    ('Veg Spring Rolls',       'Starters',       Decimal('220.00'), True),
    ('Hara Bhara Kebab',       'Starters',       Decimal('260.00'), False),  # out of stock
    ('Butter Chicken',         'Main Course',    Decimal('420.00'), True),
    ('Paneer Butter Masala',   'Main Course',    Decimal('360.00'), True),
    ('Dal Makhani',            'Main Course',    Decimal('290.00'), True),
    ('Chana Masala',           'Main Course',    Decimal('250.00'), True),
    ('Rogan Josh',             'Main Course',    Decimal('480.00'), True),
    ('Malai Kofta',            'Main Course',    Decimal('340.00'), False),
    ('Garlic Naan',            'Breads',         Decimal('70.00'),  True),
    ('Butter Naan',            'Breads',         Decimal('60.00'),  True),
    ('Tandoori Roti',          'Breads',         Decimal('40.00'),  True),
    ('Laccha Paratha',         'Breads',         Decimal('80.00'),  True),
    ('Veg Biryani',            'Rice & Biryani', Decimal('320.00'), True),
    ('Chicken Biryani',        'Rice & Biryani', Decimal('380.00'), True),
    ('Jeera Rice',             'Rice & Biryani', Decimal('180.00'), True),
    ('Curd Rice',              'Rice & Biryani', Decimal('160.00'), True),
    ('Gulab Jamun',            'Desserts',       Decimal('120.00'), True),
    ('Gajar Ka Halwa',         'Desserts',       Decimal('150.00'), True),
    ('Rasmalai',               'Desserts',       Decimal('140.00'), False),
]

# Food subclass rows: (name, category, price, available, is_vegetarian, spice_level)
FOODS = [
    ('Chilli Paneer',   'Starters',    Decimal('300.00'), True, True,  4),
    ('Mutton Seekh',    'Starters',    Decimal('360.00'), True, False, 3),
    ('Veg Manchurian',  'Main Course', Decimal('270.00'), True, True,  2),
]

# Beverage subclass rows: (name, category, price, available, size_ml, is_carbonated)
BEVERAGES = [
    ('Masala Chai',     'Beverages', Decimal('40.00'),  True, 150, False),
    ('Sweet Lassi',     'Beverages', Decimal('90.00'),  True, 300, False),
    ('Fresh Lime Soda', 'Beverages', Decimal('80.00'),  True, 250, True),
    ('Cola',            'Beverages', Decimal('60.00'),  True, 330, True),
]


class Command(BaseCommand):
    help = 'Seed the database with sample menu items and orders'

    def add_arguments(self, parser):
        # argparse under the hood — same idea as commander/yargs flags in Node.
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Delete existing orders + menu items before seeding',
        )

    @transaction.atomic  # all-or-nothing: a failure halfway rolls the whole thing back
    def handle(self, *args, **options):
        if options['fresh']:
            # Order matters: OrderItem.menu_item is PROTECT, so menu items
            # can't be deleted while an order line still points at them.
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            MenuItem.objects.all().delete()  # also clears Food/Beverage child rows
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('Wiped existing sample data.'))

        categories = {}
        for name, desc in CATEGORIES.items():
            # get_or_create = find-or-insert; returns (obj, created_bool)
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={'description': desc}
            )
            categories[name] = cat

        created_items = []

        for name, cat, price, available in MENU_ITEMS:
            item, was_created = MenuItem.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[cat],
                    'price': price,
                    'is_available': available,
                    'description': f'{name} — a house favourite.',
                },
            )
            if was_created:
                created_items.append(item)

        for name, cat, price, available, veg, spice in FOODS:
            item, was_created = Food.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[cat],
                    'price': price,
                    'is_available': available,
                    'is_vegetarian': veg,
                    'spice_level': spice,
                    'description': f'{name} — spice level {spice}/5.',
                },
            )
            if was_created:
                created_items.append(item)

        for name, cat, price, available, size, fizzy in BEVERAGES:
            item, was_created = Beverage.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[cat],
                    'price': price,
                    'is_available': available,
                    'size_ml': size,
                    'is_carbonated': fizzy,
                    'description': f'{name} — {size}ml.',
                },
            )
            if was_created:
                created_items.append(item)

        # Spread created_at over the past ~25 days so ?ordering=created_at and
        # ?ordering=-created_at actually show a difference. created_at is
        # auto_now_add (write-once on insert), so we override it here with an
        # explicit .update() — which, unlike .save(), does NOT re-fire auto_now.
        now = timezone.now()
        for offset, item in enumerate(created_items):
            MenuItem.objects.filter(pk=item.pk).update(
                created_at=now - timedelta(days=offset, hours=offset)
            )

        self._seed_orders(now)

        self.stdout.write(self.style.SUCCESS(
            f'Done. {Category.objects.count()} categories, '
            f'{MenuItem.objects.count()} menu items, '
            f'{Order.objects.count()} orders.'
        ))

    def _seed_orders(self, now):
        """A few orders with line items, so the orders endpoints have data."""
        if Order.objects.exists():
            return  # don't pile up duplicate orders on rerun

        available = list(MenuItem.objects.filter(is_available=True)[:12])
        if not available:
            return

        sample_orders = [
            ('Aarav Sharma',  '9876543210', 'aarav@example.com',  'delivered', [0, 4, 10]),
            ('Diya Patel',    '9823456781', 'diya@example.com',   'preparing', [5, 6, 11, 18]),
            ('Kabir Singh',   '9911223344', 'kabir@example.com',  'pending',   [1, 14]),
            ('Meera Nair',    '9765432180', 'meera@example.com',  'confirmed', [7, 8, 12, 19]),
        ]

        for name, phone, email, status, idxs in sample_orders:
            order = Order.objects.create(
                customer_name=name,
                customer_phone=phone,
                customer_email=email,
                status=status,
            )
            total = Decimal('0.00')
            for i in idxs:
                item = available[i % len(available)]
                qty = 1 + (i % 3)
                OrderItem.objects.create(
                    order=order,
                    menu_item=item,
                    quantity=qty,
                    unit_price=item.price,
                )
                total += item.price * qty
            # total_amount isn't auto-computed — the app is responsible for it
            order.total_amount = total
            order.save(update_fields=['total_amount'])
