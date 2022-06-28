from django.contrib import admin
from .models import Order, Payment, OrderProduct
# Register your models here.


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('payment',
                        'user', 
                        'product', 
                        'variation', 
                        'quantity',
                        'product_price',
                        'ordered'
                        )


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number',
                    'first_name',
                    'phone',
                    'email',
                    'status',
                    'is_ordered'
                    ]
    list_filter = ['is_ordered', 'status']
    search_fields = ['first_name','phone','email','order_number']
    list_per_page = 22
    inlines = [OrderProductInline]

admin.site.register(Payment)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderProduct)