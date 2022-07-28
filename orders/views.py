import datetime
from django.shortcuts import render, redirect
from cart.models import CartItem
from store.models import Product
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from django.contrib import messages
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import JsonResponse


def order_completed(request, order, payment):
    # After payment move ordered items into orderProduct table
    user = request
    cart_items = CartItem.objects.filter(user=user)

    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user = user
        order_product.product_id = item.product.id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        # Set variation of item
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variation.set(product_variation)
        order_product.save()

        # Decrease the quantity of sold product
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart items after successful order
    CartItem.objects.filter(user=user).delete()

    # Send successful order email to user
    mail_subject = "Thank you for your order!"
    message = render_to_string(
        "orders/order_successful_email.html",
        {
            "user": user,
            "order": order,
        },
    )
    to_email = user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()


def payments(request):
    user = request.user
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, is_ordered=False, order_number=body["orderID"]
    )

    payment = Payment(
        user=request.user,
        Payment_id=body["transID"],
        Payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body["status"],
    )
    payment.save()

    order.Payment = payment
    order.is_ordered = True
    order.save()
    order_completed(user, order, payment)

    data = {
        "order_number": order.order_number,
        "transID": payment.Payment_id,
    }
    return JsonResponse(data)


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
            if order:
                print("inside if--------", order.order_number)
                request.session["order_id"] = order_number

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


def order_success(requset):
    order_number = requset.GET.get("order_number")
    transID = requset.GET.get("payment_id")

    try:
        order = Order.objects.get(
            order_number=order_number, is_ordered=True
        )
        order_product = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(Payment_id=transID)

        sub_total = 0
        for i in order_product:
            sub_total += i.product_price * i.quantity

        context = {
            "order": order,
            "order_product": order_product,
            "order_number": order.order_number,
            "transID": payment.Payment_id,
            "payment": payment,
            "sub_total": sub_total,
        }
        return render(requset, "orders/order_success.html", context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect("home")


def cash_on_delivery(requset):
    if requset.method == "POST":
        try:
            order_id = requset.session["order_id"]
        except:
            pass
        order = Order.objects.get(
            user=requset.user, is_ordered=False, order_number=order_id
        )
        user = requset.user

        payment = Payment(
            user=user,
            Payment_id=order_id,
            Payment_method="Cash on delivery",
            amount_paid=order.order_total,
            status="Ordered",
        )
        payment.save()

        order.Payment = payment
        order.is_ordered = True
        order.save()
        order_completed(user, order=order, payment=payment)
        context = {
            "order": order,
            "payment": payment,
        }
    return render(requset, "orders/order_success.html", context)
