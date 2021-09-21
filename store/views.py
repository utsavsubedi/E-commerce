from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Product
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
# Create your views here.

def store(request, category_slug=None):
    category = None
    product_objects = None

    if category_slug!= None:
        category = get_object_or_404(Category, slug=category_slug)
        product_objects = Product.objects.all().filter(category = category, is_available=True)
    
    else:
        product_objects = Product.objects.all().filter(is_available = True).order_by('id')

    paginator = Paginator(product_objects, 3)
    page = request.GET.get('page')
    product_objects = paginator.get_page(page)
    product_count = Product.objects.count()

    context = {
        'product_objects' : product_objects,
        'product_count' : product_count
    }
    return render(request, 'store/store.html', context=context)

def product_detail(request,category_slug, product_slug):
    product = Product.objects.get(category__slug = category_slug, slug=product_slug, is_available =True)
    in_cart = CartItem.objects.filter( cart__cart_id= _cart_id(request), product=product ).exists()
    context = {
        'product': product,
        "in_cart": in_cart,
    }
    return render(request, 'store/product_detail.html', context=context)


def search(request):
    if 'keyword' in  request.GET:
        keyword = request.GET.get('keyword')
        if keyword:
            product = Product.objects.order_by('-create_date').filter(Q(description__icontains = keyword) | Q(product_name__icontains=keyword))
            product_count = product.count()
    context = {
            'product_objects': product,
            'product_count': product_count,
        }
    return render(request, 'store/store.html', context=context)