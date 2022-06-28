import datetime
from django.shortcuts import render, redirect
from cart.models import CartItem
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from django.contrib import messages
import json

# Create your views here.
def payments(requset):
    body = json.loads(requset.body)
    order = Order.objects.get(
        user=requset.user, is_ordered=False, order_number=body["orderID"]
    )

    payment = Payment(
        user=requset.user,
        Payment_id=body["transID"],
        Payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body["status"],
    )
    payment.save()

    order.Payment = payment
    order.is_ordered = True
    order.save()

    # After payment move ordered items into orderProduct table
    cart_items = CartItem.objects.filter(user=requset.user)

    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user = requset.user
        order_product.product_id = item.product.id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()


    return render(requset, "orders/payments.html")


def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    item_count = cart_items.count()

    if item_count <= 0:
        return redirect("store")

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data["first_name"]
            data.last_name = form.cleaned_data["last_name"]
            data.email = form.cleaned_data["email"]
            data.phone = form.cleaned_data["phone"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.country = form.cleaned_data["country"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get("REMOTE_ADDR")
            data.save()

            # GENERATE ORDER NUMBER
            yr = int(datetime.date.today().strftime("%Y"))
            dt = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(
                user=current_user,
                is_ordered=False,
                order_number=order_number,
            )
            context = {
                "order": order,
                "total": total,
                "grand_total": grand_total,
                "tax": tax,
                "cart_items": cart_items,
            }
            return render(request, "orders/payments.html", context)
        else:
            return redirect("checkout")