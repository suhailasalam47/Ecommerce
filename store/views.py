import imp
from cart.views import _cart_id
from django.shortcuts import get_object_or_404, render, redirect
from cart.models import CartItem
from .models import Product, ProductGallery, ReviewRating
from store.models import Product
from category.models import Category
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewRatingForm
from django.contrib import messages
from orders.models import OrderProduct
# Create your views here.


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories, is_available=True
        )
        paginator = Paginator(products, 1)
        page = request.GET.get("page")
        paged_product = paginator.get_page(page)
        product_count = products.count()
    else:
        products = (
            Product.objects.all().filter(is_available=True).order_by("id")
        )
        paginator = Paginator(products, 3)
        page = request.GET.get("page")
        paged_product = paginator.get_page(page)
        product_count = products.count()

    context = {
        "products": paged_product,
        "product_count": product_count,
    }
    return render(request, "store/store.html", context)


def product_details(request, category_slug, product_slug):
    order_product = None
    products = (
            Product.objects.all().filter(is_available=True).order_by("id")
        )
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug
        )
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product
        ).exists()

    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            order_product = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except:
            order_product = None
    else:
        order_product = None

    # Get the review
    review = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    #Product Gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "order_product":order_product,
        "review": review,
        "product_gallery" : product_gallery,
        "products":products,
    }
    return render(request, "store/product_details.html", context)


def search(request):
    if "key" in request.GET:
        keyword = request.GET["key"]
        if keyword:
            products = Product.objects.order_by("-created_date").filter(
                Q(description__icontains=keyword)
                | Q(product_name__icontains=keyword)
            )
            product_count = products.count()

        context = {
            "products": products,
            "product_count": product_count,
        }
    return render(request, "store/store.html", context)


def submit_review(request, product_id):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            review = ReviewRating.objects.get(
                user__id=request.user.id, 
                product__id=product_id
                )
            form = ReviewRatingForm(request.POST, instance=review)
            form.save()
            messages.success(request, "Thank you! Your review has been updated")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewRatingForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.review = form.cleaned_data['review']
                data.rating = form.cleaned_data['rating']
                data.product_id = product_id
                data.user = request.user
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()
                messages.success(request, "Thank you for your valuable review")
                return redirect(url)

