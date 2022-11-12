
from django.contrib import messages, auth
from django.shortcuts import render, redirect,get_object_or_404

from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account, UserProfile
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderProduct, Payment

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from cart.views import _cart_id
from cart.models import Cart, CartItem
import requests
from . import twilio_client
from .twilio_client import TwilioOTP
# Create your views here.


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            password = form.cleaned_data["password"]
            username = email.split("@")[0]
            confirm_passwrd = form.cleaned_data["confirm_password"]
            print("email----", email)
            if password!=confirm_passwrd:
                messages.error(request,"Password not matching")
                return redirect("register")
            elif Account.objects.filter(email=email).exists():
                print("email-------------------")
                messages.error(request,"This Email already exist")
                return redirect("register")
            elif Account.objects.filter(phone_number=phone_number).exists():
                messages.error(request,"This Phone number already exist")
                return redirect("register")
            else:
                user = Account.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                    password=password,
                )
                user.phone_number = phone_number
                user.save()

            #USER PROFILE CREATING
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-propic.jpeg'
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            return redirect(
                "/accounts/login/?command=verification&email=" + email
            )
    else:
        form = RegistrationForm()

    context = {
        "form": form,
    }
    return render(request, "accounts/register.html", context)



def login(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(email=email, password=password)
        print(user)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exist = CartItem.objects.filter(
                    cart=cart
                ).exists()
                print(is_cart_item_exist)
                if is_cart_item_exist:
                    cart_item = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_item:
                        variation = item.variation.all()
                        product_variation.append(list(variation))

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variation.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for i in product_variation:
                        if i in ex_var_list:
                            index = ex_var_list.index(i)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass

            auth.login(request, user)
            messages.success(request, "Login successful")

            url = request.META.get("HTTP_REFERER")
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split("=") for x in query.split("&"))
                if "next" in params:
                    next_page = params["next"]
                    return redirect(next_page)
            except:
                return redirect("dashboard")

        else:
            messages.error(request, "Invalid credential")
            return redirect("login")
    return render(request, "accounts/login.html")


def phone_validation(request):
    if request.method == 'POST':
        phone = request.POST['phone']
        request.session['phone'] = phone
        if Account.objects.filter(phone_number=phone).exists():
            obj = TwilioOTP()
            obj.send(phone)
            return redirect("otp_verification")
        else:
            messages.error(request, "Sorry, the phone number is no longer registered on this application.")
            return redirect("phone_validation")
    return render(request, "accounts/phone_submit.html")


def otp_verification(request):
    if request.method == 'POST':
        otp = request.POST['otp']
        phone = request.session['phone']

        obj = TwilioOTP()
        status = obj.check(phone,otp)
        if status == 'approved':
            user = Account.objects.get(phone_number=phone)
            print(user)
            auth.login(request, user)
            messages.success(request, "Login successful")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid OTP")
            return redirect("otp_verification")
    return render(request, "accounts/otp_verification.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out ")
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(
        user, token
    ):
        user.is_active = True
        user.save()
        messages.success(
            request, "Congratulations! Your account is activated"
        )
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link")
        return redirect("register")


@login_required(login_url="login")
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    order_count = orders.count()
    user_profile = UserProfile.objects.get(user_id=request.user.id)
    context={
        'order_count':order_count,
        "user_profile" : user_profile,
    }
    return render(request, "accounts/dashboard.html", context)


def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # RESET PASSWORD EMAIL
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string(
                "accounts/reset_password_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(
                request,
                "Reset password email has been sent to your email address",
            )
            return redirect("login")
        else:
            messages.error(request, "Account does not exist")
            return redirect("forgot_password")
    return render(request, "accounts/forgot_password.html")


def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(
        user, token
    ):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password")
        return redirect("reset_password")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("login")


def reset_password(request):
    if request.method == "POST":
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password == password2:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Reset password successful")
            return redirect("login")

        else:
            messages.error(request, "Password not matching!")
            return redirect("reset_password")
    else:
        return render(request, "accounts/reset_password.html")


@login_required(login_url="login")
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders':orders,
    }
    return render(request,"accounts/my_orders.html", context)


@login_required(login_url="login")
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,"Your profile has been updated.")
            return redirect("edit_profile")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "user_profile":user_profile,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_pswrd"]
        new_password = request.POST["new_pswrd"]
        confirm_password = request.POST["confirm_pswrd"]

        user = Account.objects.get(email__exact=request.user.email)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password changed successfully")
                return redirect("change_password")
            else:
                messages.error(
                    request, "Please enter valid current password"
                )
                return redirect("change_password")
        else:
            messages.error(request, "Password does not match")
            return redirect("change_password")

    return render(request, "accounts/change_password.html")


@login_required(login_url="login")
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    sub_total = 0
    for i in order_detail:
        sub_total += i.product_price * i.quantity
    context = {
        "order_detail":order_detail,
        "order":order,
        "sub_total":sub_total,
    }
    return render(request, "accounts/order_detail.html", context)

