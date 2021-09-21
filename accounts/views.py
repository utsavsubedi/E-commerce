
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import Account
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from carts.models import Cart, CartItem
from carts.views import _cart_id
import requests

#Verification email import 
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, message

def register(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            phone_number = form.cleaned_data['phone_number']
            username = email.split('@')[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name,
                                    email=email, username=username, password=password )

            user.phone_number = phone_number
            user.save()

            #user activation
            current_site = get_current_site(request)
            mail_to = email
            subject = "Please activate your account"
            message = render_to_string('accounts/verify_email.html',{
                'user' : user,
                'domain': current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),
            })
            confirmation_email = EmailMessage(subject, message, to=[mail_to])
            confirmation_email.send()

            messages.success(request, 'Your account is created successfully.')
            return redirect('/register/?command=verification&email='+email)
    else:
        form = RegisterForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context=context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # product variation of not logged in user
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # product variation of logged in user, and corresponding item id 
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    
                    #if common variation, add 1 to quantity else save new variations user 
                    for product in product_variation:
                        if product in ex_var_list:
                            index = ex_var_list.index(product)
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
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            print(url)
            try:
                query = requests.utils.urlparse(url).query
                print(query)
                params = dict( x.split('=') for x in query.split('&'))
                print(params)
                if 'next' in params:
                    next_page = params['next']
                    print(next_page)
                    return redirect(next_page)
            except:
                return redirect('dashboard')
            
            
    return render(request, 'accounts/login.html')


@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager(pk = uid)
    except(TypeError, OverflowError, ValueError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! your acccount was created.')
        redirect('login')
    else:
        messages.success(request, 'Sorry! The activation link was wrong.')
        redirect('register') 

    return HttpResponse('okay')

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            #forgot password email
            current_site = get_current_site(request)
            mail_to = email
            subject = "Forgot Password"
            message = render_to_string('accounts/reset_password_validate.html',{
                'user' : user,
                'domain': current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),
            })
            confirmation_email = EmailMessage(subject, message, to=[mail_to])
            confirmation_email.send()
            messages.success(request, 'Check your email to reset your password')
            return redirect('login')
            
        else:
            messages.error(request, 'The account doesnot exists!')
            return redirect('forgot-password')
    return render(request, 'accounts/forgot-password.html')

def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager(pk = uid)
    except(TypeError, OverflowError, ValueError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password.')
        return redirect('resetPassword')
        
    else:
        messages.success(request, 'Sorry! The link has expired')
        return redirect('forgot-password')
        

    return HttpResponse('okay')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk = uid)
            user.set_password(password)
            messages.success(request, 'Passowrd reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset-password')
    else:
        return render(request, 'accounts/reset-password.html')


        