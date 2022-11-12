from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Count


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    # get the product
    product = Product.objects.get(id=product_id)
    current_user = request.user

    if current_user.is_authenticated:
        product_variation = []

        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
                print("key=",key,"value=",value)

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value,
                    )
                    product_variation.append(variation)
                except:
                    pass
        color = product_variation[0].variation_value
        size = product_variation[1].variation_value

        cart_item = CartItem.objects.filter(
                product=product, user=current_user,variation__variation_value = color
            ).filter( variation__variation_value = size)
        print(cart_item)
        if cart_item.exists():
            cart_item = cart_item.first()
            cart_item.quantity+=1
            cart_item.save()
        else:
            cart_item= cart_item.first()
            cart_item = CartItem.objects.create(
                    product=product, quantity=1, user=current_user
                )
            cart_item.variation.add(*product_variation)
            cart_item.save()
        return redirect("cart")

    else:
        product_variation = []

        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value,
                    )
                    product_variation.append(variation)
                except:
                    pass

        try:
            # get the cart using the cart id present in the session
            cart = Cart.objects.get(cart_id=_cart_id(request))

        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
        color = product_variation[0].variation_value
        size = product_variation[1].variation_value

        cart_item = CartItem.objects.filter(
                product=product, cart=cart,variation__variation_value = color
            ).filter( variation__variation_value = size)
        if cart_item.exists():
            cart_item = cart_item.first()
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = cart_item.first()
            cart_item = CartItem.objects.create(
                product = product,
                cart = cart,
                quantity=1
            )
            cart_item.variation.add(*product_variation)
            cart_item.save()
        return redirect("cart")
        

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product, user=request.user, id=cart_item_id
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(
                product=product, cart=cart, id=cart_item_id
            )

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product, user=request.user, id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(
            product=product, cart=cart, id=cart_item_id
        )
    cart_item.delete()
    return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = None
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = None
    grand_total = 0
    
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
            print(cart_item.product," = ",cart_item.quantity)
       
        print("cart items-----",cart_items.values())

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    cart_product = cart_items.values('product_id').annotate(dcount=Count('product_id')).order_by()
    print("cart_product=======", cart_product)
    for i in cart_product:
        print(i['product_id'])
        print(cart_items.filter(product_id=i['product_id']).values('quantity'))
    return render(request, "store/checkout.html", context)
