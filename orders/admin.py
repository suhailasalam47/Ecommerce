from django.contrib import admin
from .models import Order, Payment, OrderProduct
# Register your models here.


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','first_name','phone','email','status','is_ordered']
    list_filter = ['is_ordered', 'status']
    search_fields = ['first_name','phone','email','order_number']
    list_per_page = 22

admin.site.register(Payment)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderProduct)