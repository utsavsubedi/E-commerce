from django.contrib import admin
from .models import Payment, Order, OrderProduct


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'order', 'product', 'variations')
    extra = 0



class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'first_name', 'last_name', 'phone', 'email', 'order_total']
    list_filter = ['order_number', 'first_name', 'last_name', 'city', 'is_ordered', 'country']
    search_fields = ['order_number', 'first_name', 'last_name', 'email']
    list_per_page = 40
    inlines = [OrderProductInline]


admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)


