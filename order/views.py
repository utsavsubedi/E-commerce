from order.forms import OrderForm
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from carts.models import CartItem

from .models import Order, OrderProduct, Payment
import datetime
from store.models import Product
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Create your views here.
def place_order(request, total =0, quantity =0):
    current_user = request.user

    
    cart_items = CartItem.objects.filter(user = current_user)
    item_count = cart_items.count()
    if item_count < 0:
        return redirect('store')


    for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity

    tax = (0.02 * total)
    grand_total = tax+total

    if request.method == 'POST':
        # print('true')
        form = OrderForm(request.POST)
        # print(form.is_valid())
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data.get('first_name')
            data.last_name = form.cleaned_data.get('last_name')
            data.email = form.cleaned_data.get('email')
            data.phone = form.cleaned_data.get('phone')
            data.address_line_1 = form.cleaned_data.get('address_line_1')
            data.address_line_2 = form.cleaned_data.get('address_line_2')
            data.city = form.cleaned_data.get('city')
            data.state = form.cleaned_data.get('state')
            data.order_note = form.cleaned_data.get('order_note')
            data.country = form.cleaned_data.get('country')
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            #order number generation
            today = str(datetime.date.today()).split('-')
            today = ''.join(today)
            order_number = today+str(data.id)
            data.order_number = order_number
            # print('not_saved')
            data.save()
            # print('saved')

            order = Order.objects.get(user=current_user, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total':total,
                'grand_total':grand_total,
                'tax':tax,
            }

            return render(request, 'order/payment.html', context)
        else:
            return redirect('checkout')

            

    return HttpResponse('okay')


def payment(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    # mail_subject = 'Thank you for your order!'
    # message = render_to_string('order/order_received_email.html', {
    #     'user': request.user,
    #     'order': order,
    #     })
    # to_email = request.user.email
    # send_email = EmailMessage(mail_subject, message, to=[to_email])
    # send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'order/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')