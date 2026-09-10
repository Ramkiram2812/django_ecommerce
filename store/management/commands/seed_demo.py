from django.core.management.base import BaseCommand
from store.models import Category, Product

DATA = {
    "Sneakers": [
        ("Urban Runner X", "Lightweight everyday sneaker with breathable mesh.", 3499, 4499, "products/product-1.svg"),
        ("Street Pro", "Cushioned street sneaker designed for all-day comfort.", 4299, 5299, "products/product-2.svg"),
        ("Aero Knit", "Flexible knit upper with a soft responsive sole.", 2999, 3999, "products/product-3.svg"),
    ],
    "Headphones": [
        ("Wave ANC", "Wireless over-ear headphones with active noise cancellation.", 5999, 7499, "products/product-4.svg"),
        ("Bass Mini", "Compact wireless headphones with punchy bass.", 2499, 3299, "products/product-5.svg"),
    ],
    "Smart Gear": [
        ("Pulse Watch", "Fitness smartwatch with heart-rate and activity tracking.", 6999, 8499, "products/product-6.svg"),
        ("Fit Band 3", "Slim activity band with sleep and workout tracking.", 1999, 2499, "products/product-7.svg"),
    ],
    "Bags": [
        ("Metro Backpack", "Water-resistant backpack with laptop compartment.", 2799, 3499, "products/product-8.svg"),
    ],
}

class Command(BaseCommand):
    help = "Create demo categories and products"

    def handle(self, *args, **options):
        for category_name, products in DATA.items():
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": category_name.lower().replace(" ", "-")}
            )
            for i, (name, desc, price, old_price, image) in enumerate(products):
                Product.objects.update_or_create(
                    slug=name.lower().replace(" ", "-"),
                    defaults={
                        "category": category,
                        "name": name,
                        "description": desc,
                        "price": price,
                        "old_price": old_price,
                        "image": image,
                        "stock": 20,
                        "featured": i == 0,
                    }
                )
        self.stdout.write(self.style.SUCCESS("Demo store data created successfully."))
