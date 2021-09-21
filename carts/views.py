from order.forms import OrderForm
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user

    product = Product.objects.get(id=product_id)
    product_variation = []
    if request.method == 'POST':
        size = request.POST['size']
        color = request.POST['color']
        print(color, size)
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try: 
                variation = Variation.objects.get(product=product,variation_category__iexact =key, variation_value__iexact=value)
                product_variation.append(variation)
                print(product_variation)

            except:
                pass
    # return HttpResponse('color')
    product = Product.objects.get(id=product_id)


    #if user if authenticated
    if current_user.is_authenticated:

        cart_item_exists = CartItem.objects.filter(user=current_user, product=product).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ext_var_list = []
            item_id = []
            for item in cart_item:
                variation = item.variations.all()
                ext_var_list.append(list(variation))
                item_id.append(item.id)

            if product_variation in ext_var_list:
                index = ext_var_list.index(product_variation)
                id = item_id[index]
                cart_item = CartItem.objects.get(product=product, user=current_user, id = id)
                cart_item.quantity += 1
                cart_item.save()

            else:
                cart_item = CartItem.objects.create(product=product, user=current_user, quantity = 1)
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, user=current_user, quantity = 1)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        

        return redirect('carts')
    else:
        try:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart.save()
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id = _cart_id(request))
            cart.save()

        cart_item_exists = CartItem.objects.filter(cart=cart, product=product).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ext_var_list = []
            item_id = []
            for item in cart_item:
                variation = item.variations.all()
                ext_var_list.append(list(variation))
                item_id.append(item.id)

            if product_variation in ext_var_list:
                index = ext_var_list.index(product_variation)
                id = item_id[index]
                cart_item = CartItem.objects.get(product=product, cart=cart, id = id)
                cart_item.quantity += 1
                cart_item.save()

            else:
                cart_item = CartItem.objects.create(product=product, cart=cart, quantity = 1)
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, cart=cart, quantity = 1)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        

        return redirect('carts')


def remove_cart(request, product_id, cart_item_id):
    current_user = request.user
    
    product = get_object_or_404(Product, id=product_id)
    if current_user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user =current_user, id = cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id = cart_item_id)

    
    try:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('carts')

def remove_cart_item(request, product_id, cart_item_id):
    current_user = request.user
    product = Product.objects.get(id = product_id)
    if current_user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user =current_user, id = cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id = cart_item_id)
    
    cart_item.delete()
    return redirect('carts')




def carts(request, total=0, quantity=0, cart_items=None):
    try:
        
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    tax = (0.02 * total)
    grand_total = tax+total
    context = {
        'total' : total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax':tax
    }
    return render(request, 'carts/carts.html', context=context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    tax = (0.02 * total)
    grand_total = tax+total
    context = {
        'total' : total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax':tax,
        
    }
    return render(request, 'carts/checkout.html', context=context)