from django.shortcuts import render, redirect
from cart.models import CartItem
from .forms import OrderForm

# Create your views here.

def place_order(request):
    current_user = request.user
    cart_item = CartItem.objects.filter(user=current_user)
    item_count = cart_item.count()

    if item_count <= 0:
        return redirect('store')

    if request.method == 'POST':
        form = OrderForm(request.POST)  