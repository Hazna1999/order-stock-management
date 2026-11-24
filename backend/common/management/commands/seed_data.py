from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product
from common.permissions import ADMIN, ALL_ROLES, INVENTORY, SALES
from customers.models import Customer

PASSWORD = "Pass@1234"

USERS = [
    ("admin1", ADMIN),
    ("sales1", SALES),
    ("sales2", SALES),
    ("inventory1", INVENTORY),
]

PRODUCTS = [
    ("Steel Bolt M8", "BOLT-M8", "Hardware", "0.25", 500, 100),
    ("Steel Nut M8", "NUT-M8", "Hardware", "0.15", 800, 100),
    ("Cordless Drill", "DRL-100", "Tools", "89.99", 25, 10),
    ("Hammer 500g", "HAM-500", "Tools", "12.50", 40, 10),
    ("Safety Gloves", "GLV-001", "Safety", "4.75", 120, 30),
    ("Safety Helmet", "HLM-001", "Safety", "15.00", 8, 10),
    ("Measuring Tape 5m", "TAP-5M", "Tools", "6.40", 60, 15),
]

CUSTOMERS = [
    ("Acme Traders", "orders@acme.com", "+91 484 000 1001"),
    ("Bright Constructions", "buy@bright.com", "+91 484 000 1002"),
    ("City Hardware", "stock@cityhw.com", "+91 484 000 1003"),
]


class Command(BaseCommand):
    help = "Load sample users, products and customers (safe to run repeatedly)."
       

    @transaction.atomic
    def handle(self, *args, **options):
        for role_name in ALL_ROLES:
            Group.objects.get_or_create(name=role_name)
            
        for username, role in USERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(PASSWORD)
                user.save()
            user.groups.add(Group.objects.get(name=role))

        for name, sku, category, price, stock, reorder in PRODUCTS:
            if not Product.objects.filter(sku__iexact=sku).exists():
                Product.objects.create(
                    name=name, sku=sku, category=category, unit_price=price,
                    stock_quantity=stock, reorder_level=reorder,
                )

        for name, email, phone in CUSTOMERS:
            if not Customer.objects.filter(email__iexact=email).exists():
                Customer.objects.create(name=name, email=email, phone=phone)

        self.stdout.write(self.style.SUCCESS("Sample data loaded."))
        self.stdout.write(f"Users (password {PASSWORD}): " + ", ".join(u for u, _ in USERS))