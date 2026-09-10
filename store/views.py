from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from .models import Category, Product, Order, OrderItem

def cart_data(request):
    raw = request.session.get("cart", {})
    ids = [int(k) for k in raw.keys()]
    products = Product.objects.filter(id__in=ids).select_related("category")
    items, total, count = [], Decimal("0"), 0
    for product in products:
        qty = max(1, int(raw.get(str(product.id), 1)))
        qty = min(qty, product.stock)
        subtotal = product.price * qty
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})
        total += subtotal
        count += qty
    return items, total, count

def base_context(request):
    _, _, count = cart_data(request)
    return {"categories": Category.objects.all(), "cart_count": count}

def home(request):
    products = Product.objects.filter(featured=True, stock__gt=0)[:8]
    context = base_context(request)
    context["products"] = products
    return render(request, "store/home.html", context)

def product_list(request):
    qs = Product.objects.select_related("category").filter(stock__gt=0)
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(description__icontains=q)
    if category:
        qs = qs.filter(category__slug=category)
    context = base_context(request)
    context.update({"products": qs, "search": q, "selected_category": category})
    return render(request, "store/product_list.html", context)

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    qs = Product.objects.filter(category=category, stock__gt=0)
    context = base_context(request)
    context.update({"products": qs, "category": category})
    return render(request, "store/product_list.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(category=product.category, stock__gt=0).exclude(pk=product.pk)[:4]
    context = base_context(request)
    context.update({"product": product, "related": related})
    return render(request, "store/product_detail.html", context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = max(1, int(request.POST.get("quantity", 1)))
    cart = request.session.get("cart", {})
    current = int(cart.get(str(product_id), 0))
    cart[str(product_id)] = min(current + qty, product.stock)
    request.session["cart"] = cart
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.POST.get("next") or "cart")

def cart(request):
    items, total, count = cart_data(request)
    context = base_context(request)
    context.update({"items": items, "total": total, "cart_count": count})
    return render(request, "store/cart.html", context)

def update_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = max(1, min(int(request.POST.get("quantity", 1)), product.stock))
    cart = request.session.get("cart", {})
    cart[str(product_id)] = qty
    request.session["cart"] = cart
    return redirect("cart")

def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart.pop(str(product_id), None)
    request.session["cart"] = cart
    return redirect("cart")

@transaction.atomic
def checkout(request):
    items, total, count = cart_data(request)
    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect("product_list")
    if request.method == "POST":
        order = Order.objects.create(
            full_name=request.POST.get("full_name", "").strip(),
            email=request.POST.get("email", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            address=request.POST.get("address", "").strip(),
            city=request.POST.get("city", "").strip(),
            pincode=request.POST.get("pincode", "").strip(),
            total=total,
        )
        for item in items:
            OrderItem.objects.create(order=order, product=item["product"],
                                     price=item["product"].price, quantity=item["quantity"])
            item["product"].stock -= item["quantity"]
            item["product"].save(update_fields=["stock"])
        request.session["cart"] = {}
        return redirect("order_success", order_id=order.id)
    context = base_context(request)
    context.update({"items": items, "total": total, "cart_count": count})
    return render(request, "store/checkout.html", context)

def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    context = base_context(request)
    context["order"] = order
    return render(request, "store/order_success.html", context)
