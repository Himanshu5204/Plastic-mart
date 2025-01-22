from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.paginator import Paginator
from django.views import View
from django.db.models import Count
from .helpers import send_forgot_password_mail
import uuid
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash,get_user_model
from .forms import ChangePasswordForm
from .models import *
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Sum
from django.http import HttpResponse
import random
from django.http import JsonResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .forms import ProductReviewForm 
from reportlab.lib.units import inch 
from .models import Order 
from PIL import Image 
from reportlab.platypus import Table, TableStyle 
from reportlab.lib import colors 
from reportlab.lib.styles import getSampleStyleSheet


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations your account is activated')
        return redirect('login')
    else:
        messages.error(request, "Invalid activation link")

def login_page(request):
    if request.method == "POST":
        uname = request.POST.get('username')
        pass1 = request.POST.get('password')

        user = authenticate(request, username=uname, password=pass1)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, "Username or password is incorrect")

    return render(request, "login.html")

def logout_page(request):
    logout(request)
    return redirect('/login/')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Get email from form data
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, "Password reset email has been sent to your email address.")
            return redirect('login')  # Redirect to login page
        else:
            messages.error(request, "Account does not exist")
            return redirect('forgot_password')  # Redirect back to forgot password page
    return render(request, "forgot_password.html")  # Render the forgot password form


def password_reset_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token): 
        request.session['uid'] = uid
        messages.success(request, "Please reset your password")
        return redirect('reset_password')
    else:
        messages.error(request, "This link has expired")
        return redirect('login')

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(id=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successfully")
            return redirect('login')
        else:
            messages.error(request, "Passwords do not match")
            return redirect('reset_password')
    else:
        return render(request, "reset_password.html")

def homepage(request):
    category = Category.objects.filter(status=0)
    product = Product.objects.all()
    paginator = Paginator(product, 8)
    page_number = request.GET.get('page')
    product_data_final = paginator.get_page(page_number)
    totalpage = product_data_final.paginator.num_pages
    context = {
        'category': category,
        'product': product,
        "productsdata": product_data_final,
        "listpage": [n+1 for n in range(totalpage)]
    }
    return render(request, "index.html", context)

def shop(request): 
    category = Category.objects.filter(status=0)
    product = Product.objects.all()
    paginator = Paginator(product, 8)
    page_number = request.GET.get('page')
    product_data_final = paginator.get_page(page_number)
    totalpage = product_data_final.paginator.num_pages
       
    context = {
        'category': category,
        'product': product,
        "productsdata": product_data_final,
        "listpage": [n+1 for n in range(totalpage)],
        "active_category_id": request.GET.get('c_id')  # Get the category_id from the URL
    }
    print("Request GET parameters:", request.GET.get('c_id'))
    return render(request, "shop.html", context)



def product_description(request, p_id): 
    category = Category.objects.filter(status=0) 
    productdetail = Product.objects.filter(id=p_id) 
 
    product = get_object_or_404(Product, id=p_id) 
    related_products = Product.objects.filter(category=product.category).exclude(id=p_id) 
    reviews = ProductReview.objects.filter(product=product) 
     
    context = { 
        'productdetail': productdetail, 
        'product': product, 
        'category': category, 
        'related_products': related_products, 
        'reviews': reviews 
    } 
     
    return render(request, "product_description.html", context)

def post_comment(request, product_id): 
    if request.method == 'POST': 
        form = ProductReviewForm(request.POST) 
        if form.is_valid(): 
            product = Product.objects.get(id=product_id) 
            review = form.save(commit=False) 
            review.product = product 
            review.user = request.user  # Assuming users     are logged in to post reviews 
            review.save() 
            messages.success(request, 'Review posted successfully.') 
            return redirect('product_description',product_id) 
    else: 
        form = ProductReviewForm() 
    return render(request, 'product_description.html', {'form': form})


def _cart_id(request): 
    cart=request.session.session_key 
    if not cart: 
        cart=request.session.create() 
    return cart 
 
 
# def cart(request): 
#     total = 0 
#     quantity = 0 
#     tax = 0 
#     grand_total = 0 
#     cart_items = [] 
#     # products=Product.objects.all() 
#     product=[] 
#     try: 
#         if request.user.is_authenticated: 
#             # cart_items = CartItems.objects.filter(user=request.user) 
#             cart_items=CartItems.objects.all()
#         else: 
#             cart = Cart.objects.get(id=_cart_id(request)) 
#             cart_items = CartItems.objects.filter(cart=cart) 
 
#         for cart_item in cart_items: 
#             total += (cart_item.product.selling_price * cart_item.quantity) 
#             quantity += cart_item.quantity 
#         tax=10    
#         grand_total = total + tax  # Add tax to the total 
#         # print("grand_total",grand_total) 
#         product = [item.product for item in cart_items] 
#     except Cart.DoesNotExist: 
#         pass 
#     except CartItems.DoesNotExist: 
#         pass    
#     except: 
#         pass 
#     # cart_items=CartItems.objects.filter(id=request.user.id) 
#     cart_items=CartItems.objects.all() 
#     # print("cart itemmm",cart_items) 
#     # print("product",product) 
#     # print("price",CartItems.sub_total)
    
#     # print("price",Cart.get_cart_total)
#     print("grand_total",grand_total)
#     print("totall",total)
#     context = { 
#         'total': total, 
#         'quantity': quantity, 
#         'product':product, 
#         'cart_items': cart_items, 
#         'grand_total': grand_total 
#     } 
#     return render(request, 'cart.html', context) 

def cart(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    cart_items = []

    try:
        user = request.user
        cart = Cart.objects.get(user=user, is_paid=False)
        # Retrieve all cart items for the current user 
        cart_items = CartItems.objects.filter(cart=cart)
        # cart_items=CartItems.objects.all()
        for cart_item in cart_items:
            total += (cart_item.product.selling_price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (total*10)/100
        grand_total = total + tax
      # print("cart itemmm",cart_items) 
      # print("product",product) 
      # print("price",CartItems.sub_total)
      # print("sppp",cart_item.get_product_price)
    except Cart.DoesNotExist:
        pass
    except CartItems.DoesNotExist:
        pass
    except:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'tax': tax,
        'cart_items': cart_items,
        'grand_total': grand_total
    }
    return render(request, 'cart.html', context)



def add_to_cart(request, p_id): 
    if request.user.is_authenticated:
        product = Product.objects.get(id=p_id) 
        user = request.user 
        cart, _ = Cart.objects.get_or_create(user=user, is_paid=False) 

        # Check if the product is already in the cart
        cart_item, created = CartItems.objects.get_or_create(cart=cart, product=product)

        # If the product is already in the cart, increase the quantity
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item.save() 

        cart_counter = CartItems.objects.filter(cart=cart).aggregate(product_count=Count('product', distinct=True))['product_count']        
        print("cartttttttt",cart_counter)
        # Add a success message
        messages.success(request, f"{product.p_name} has been added to your cart.")
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'),{'cart_counter':cart_counter})

    else:
        # If the user is anonymous, redirect to the login page without the next parameter
        return redirect('login')

def update_cart_item(request):
    user = request.user
    curr_user = cust.objects.filter(cust_id=user).first()
    cart = Cart.objects.filter(user=user).first()
    
    if request.method == 'POST':
        quantities = request.POST.getlist('quantity')
        
        for cart_item, quantity in zip(cart.cart_items.all(), quantities):
            try:
                new_quantity = int(quantity)
                print("new",new_quantity)
                if new_quantity > 0:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    
                else:
                    messages.error(request, 'Invalid quantity.')
            except ValueError:
                messages.error(request, 'Invalid quantity.')
        messages.success(request, 'Cart items updated successfully.')
        return redirect('cart')
    
    return render(request, "cart.html", {'curr_user': curr_user, 'cart_items': cart.cart_items.all()})

def remove_cart(request,p_id): 
   try: 
      cart_item=CartItems.objects.get(id = p_id) 
      print("cart",cart_item) 
      print("Cart item to be deleted:", cart_item) 
      cart_item.delete() 
   except CartItems.DoesNotExist: 
        print("Cart item does not exist") 
   except Exception as e: 
       print(e) 
       return HttpResponseRedirect(request.META.get('HTTP_REFERER')) 
   return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='login')
def checkout(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    cart_items = []
    try:
        user = request.user
        cart = Cart.objects.get(user=user, is_paid=False)
        cart_items = CartItems.objects.filter(cart=cart)
        for cart_item in cart_items:
            total += (cart_item.product.selling_price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (total * 10) / 100
        grand_total = total + tax
    except Cart.DoesNotExist:
        pass
    except CartItems.DoesNotExist:
        pass
    
    # Redirect to shop page if total is 0
    if total == 0:
        return redirect('shop')

    curr_user = cust.objects.filter(cust_id=user)
    curruser = cust.objects.filter(cust_id=user).first()
    userprofile = cust.objects.filter(cust_id=request.user).first()
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'curr_user': curr_user,
        'curruser': curruser,
        'tax':tax,
        'userprofile': userprofile
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='login')
def placeorder(request):
    if request.method == "POST":
        print("POST request received for placeorder view.")
        curruser = request.user
        print("Current user:", curruser)
        
        # Add more print statements to check the values of other variables
        
        if not curruser.first_name:
            curruser.first_name = request.POST.get('fname')
            curruser.last_name = request.POST.get('lname')
            curruser.save()

        if not cust.objects.filter(cust_id=request.user).exists():
            userprofile = cust()
            userprofile.user = request.user
            userprofile.phone = request.POST.get('phone')
            userprofile.address = request.POST.get('address')
            userprofile.city = request.POST.get('city')
            userprofile.state = request.POST.get('state')
            userprofile.country = request.POST.get('country')
            userprofile.pincode = request.POST.get('pincode')
            userprofile.save()

        neworder = Order()
        neworder.user = request.user
        neworder.fname = request.POST.get('fname')
        neworder.lname = request.POST.get('lname')
        neworder.email = request.user.email  # Assuming email is stored in User model
        neworder.phone = request.POST.get('phone')
        neworder.address = request.POST.get('address')
        neworder.city = request.POST.get('city')
        neworder.state = request.POST.get('state')
        neworder.country = request.POST.get('country')
        neworder.pincode = request.POST.get('pincode')
        neworder.payment_mode = request.POST.get('payment_mode')
        neworder.payment_id = request.POST.get('payment_id')
        
        # Add more print statements here to debug and check values
        
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = CartItems.objects.filter(cart=cart)
        cart_total_price = sum(item.product.selling_price * item.quantity for item in cart_items)
        neworder.total_price = cart_total_price

        trackno = 'plasticmart' + str(random.randint(10000000, 99999999))
        while Order.objects.filter(tracking_no=trackno).exists():
            trackno = 'plasticmart' + str(random.randint(10000000, 99999999))
        neworder.tracking_no = trackno
        neworder.save()

        for item in cart_items:
            OrderItem.objects.create(
                order=neworder,
                product=item.product,
                price=item.product.selling_price,
                quantity=item.quantity,
                payment_status=True  # Set payment status to True for successful payment
            )
            orderproduct = Product.objects.get(id=item.product.id)
            orderproduct.quantity = orderproduct.quantity - item.quantity
            orderproduct.save()
        
        
        cart.delete()
        
        PayMode = request.POST.get('payment_mode')
        if PayMode == "Paid by  Razorpay":
            cart.is_paid = True  # Set is_paid to True for the associated cart
            cart.save()
        
            return JsonResponse({'status': "Your order has been placed successfully"})
        else:
            messages.success(request, "Your order has been placed successfully")

        return redirect('/')
    return redirect('shop')  # Redirect to some failure URL if the request method is not POST

# @login_required(login_url='login')
# def checkout(request, total=0, quantity=0, cart_item=None):
#     cart_items = []
#     try:
#         tax = 0
#         grand_total = 0
#         if request.user.is_authenticated:
#             cart_items = CartItems.objects.filter(user=request.user)
#         else:
#             cart = Cart.objects.get(id=_cart_id(request))
#             cart_items = CartItems.objects.filter(cart=cart)

#         for cart_item in cart_items:
#             total += (cart_item.Product.price * cart_item.quantity)
#             quantity += cart_item.quantity
#         tax = (2 * total) / 100
#         grand_total = total + tax
#     except:
#         pass

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'tax': tax,
#         'grand_total': grand_total
#     }
#     return render(request, 'checkout.html', context)

def thankyou(request):
    return render(request, "thankyou.html")

def profile(request):
    user = request.user
    curr_user = cust.objects.filter(cust_id=user)
    curruser = cust.objects.filter(cust_id=user).first()
    return render(request, "profile.html", {'curr_user': curr_user, 'curruser': curruser})

def service(request):
    return render(request, "services.html")

def about(request):
    return render(request, "about.html")

@login_required(login_url='login')
def contactus(request):
    company = Company.objects.first()  # Assuming you want details of the first company in the database
    context = {
        'company': company,
    }

    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        Inquiry.objects.create(
            user=user,
            fname=fname,
            lname=lname,
            email=email,
            subject=subject,
            message=message
        )
        # Add success message
        messages.success(request, 'Your inquiry has been submitted successfully!')
        return redirect('contact')

    return render(request, "contact.html", context)

# def change_password(request):  
#     if request.method == 'POST':  
#         form = ChangePasswordForm(request.POST)  
#         if form.is_valid():  
#             current_password = form.cleaned_data['current_password']  
#             new_password = form.cleaned_data['new_password']  
#             user = request.user  
  
#             # Check if the current password is correct  
#             if not user.check_password(current_password):  
#                 messages.error(request, 'Your current password is incorrect.')  
#                 return redirect('change_pass.html')  
  
#             # Change the user's password  
#             user.set_password(new_password)  
#             user.save()  
  
#             # Update the session with the new password hash  
#             update_session_auth_hash(request, user)  
  
#             messages.success(request, 'Your password was successfully updated!')  
#             return redirect('change_pass.html')  # Redirect to the change password page  
#     else:  
#         form = ChangePasswordForm()  
  
#     return render(request, 'change_pass.html', {'form': form})
def change_password(request): 
    if request.method == 'POST': 
        User = get_user_model() 
        user = User.objects.get(username=request.user.username) 
        old_password=request.POST.get('oldpassword') 
        new_password=request.POST.get('newpassword') 
        confirm_password=request.POST.get('confirmpassword') 
 
        if not old_password or not new_password or not confirm_password: 
            messages.error(request,"All fields must be filled out.") 
        elif new_password != confirm_password: 
            messages.error(request,"New password and confirm password do not match") 
        elif not user.check_password(old_password): 
            messages.error(request,"Incorrect old password. ") 
        elif user.check_password(new_password): 
            messages.error(request,"New password must be different from the old password.") 
        else: 
            user.set_password(new_password) 
            user.save() 
            update_session_auth_hash(request,user) 
            messages.success(request,"Password changed successfully..") 
        return redirect('profile') 
    return render(request, "change_pass.html")

def profile_edit(request):
    user = request.user
    curr_user = cust.objects.filter(cust_id=user).first()

    if request.method == "POST":
        if curr_user is not None:
            uname = request.POST.get('username')
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            country = request.POST.get('country')
            state = request.POST.get('state')
            city = request.POST.get('city')
            pincode = request.POST.get('pincode')

            curr_user.username = uname
            curr_user.fname = firstname
            curr_user.lname = lastname
            curr_user.phone = phone
            curr_user.email = email
            curr_user.gender = gender
            curr_user.address = address
            curr_user.state = state
            curr_user.city = city
            curr_user.pincode = pincode
            
            curr_user.save()
            return redirect('/profile/')
    return render(request, "profile_edit.html", {'curr_user': curr_user})

def create_cust(request):   
    states = State.objects.all()  # Fetch all state objects
    cities = City.objects.all()  # Fetch all city objects filter kadach
    if request.method == "POST":
        uname = request.POST.get('username')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        mobileno = request.POST.get('mobileno')
        email = request.POST.get('email')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('cpassword')
        hased_pass = make_password(pass1)

        if User.objects.filter(username=uname).exists():
            messages.error(request, 'Username already taken')
            return redirect('/create_cust/')
        if pass1 != pass2:
            messages.error(request, 'Password and Confirm password must be same !')
            return redirect('/create_cust/')
        else:
            cust_user = User.objects.create(username=uname, password=hased_pass, first_name=firstname, last_name=lastname, email=email)
            x = cust.objects.create(cust_id=cust_user, email=email, phone=mobileno, gender=gender,address=address, fname=firstname, lname=lastname)
            x.save()
            messages.error(request, "Account created successfully")
            return redirect('login')
    return render(request, 'registration.html',{'cities': cities,'states': states})

def category(request, c_id):
    category = Category.objects.all()
    products = Product.objects.filter(category_id=c_id)
    return render(request, 'product_category.html', {'category': category, 'products': products})

def home_category(request, c_id):
    category = Category.objects.all()
    products = Product.objects.filter(category_id=c_id)
    return render(request, 'home_category.html', {'category': category, 'products': products})

def Search(request):
    query = request.GET.get('query')
    results = []
    if query:
        results = Product.objects.filter(p_name__icontains=query)
    return render(request, 'search_result.html', {'results': results})

@login_required(login_url='login')
def razorpaycheck(request):
    cart = Cart.objects.filter(user=request.user).first()
    
    if cart:
        cart_items = CartItems.objects.filter(cart=cart)
        cart_total_price = 0
        for item in cart_items:
            cart_total_price += item.product.selling_price * item.quantity
        tax = (cart_total_price*10)/100
        grand_total = cart_total_price + tax
        return JsonResponse({'total_price': grand_total})
    else:
        return JsonResponse({'error': 'Cart not found'})
    
@login_required
def orders(request):
    # Assuming the user is authenticated, get the current user
    user = request.user

    # Retrieve orders for the current user
    orders = Order.objects.filter(user=user).order_by('-created_at')  # Order by created_at descending
    
    # Pass the orders to the template for rendering
    return render(request, 'orders.html', {'orders': orders})

@login_required
def view_all_products(request, order_id):
    # Get the order object associated with the order_id and the current logged-in user
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Get all products associated with the order
    products = order.orderitem_set.all()
    print("prooooo",products)
    return render(request, 'all_products.html', {'products': products})

@login_required
def cancel_order(request, order_id):
    # Get the order object associated with the order_id and the current logged-in user
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    
    # Check if the order is pending
    if order.status != 'Pending':
        messages.error(request, "Cannot cancel order. Order status is cancelled/not pending.")
        return redirect('my_orders')  # Redirect back to the orders page
    
    # Perform the cancellation logic here
    order.status = 'Cancelled'
    order.save()

    messages.success(request, "Order has been cancelled successfully.")
    return redirect('my_orders')  # Redirect back to the orders page

def generate_invoice_pdf(order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    def header(canvas, order):
        header_image_path = 'static/images/c_logo.png'  
        try:
            canvas.drawImage(header_image_path, 50, 480, width=490, height=300)  
        except OSError:
            canvas.setFont('Helvetica', 12)
            canvas.drawString(100, 750, "OM PLASTIC")
            
        # Draw company details
        canvas.setFont('Helvetica', 20)
        canvas.drawString(230, 760, "OM PLASTIC MART")
        canvas.setFont('Helvetica', 12)
        canvas.drawString(450, 760, "Mobile: +91 8511378513")
        canvas.drawString(450, 745, "Email: omplastic@gmail.com")
        canvas.drawString(160, 725, "Shade no.l, Ground Floor, Nirmit Complex, Near Kanaiya Hall,")
        canvas.drawString(145,710, "Behind Hotel Bhagyoday, Thakkarbapa Nagar, Ahmedabad 382350.")
        canvas.line(20, 700, 600, 700)
    
    # Define Footer
    def footer(canvas, order):
        canvas.drawString(inch, 0.70 * inch, "Invoice for Order {}".format(order.id))
        text_width = p.stringWidth("Thank you for shopping for our website", "Helvetica", 20)
        canvas.setFont("Helvetica", 20)
        x_coordinate = (width - text_width) / 2
        canvas.drawString(x_coordinate, 1.15 * inch, "Thank you for shopping for our website".format(order.id))
        canvas.line(20, 70, 600, 70)
        
    
    # Save canvas state before drawing header
    p.saveState()
    header(p, order)
    p.restoreState()
    
    # Write content to the PDF using ReportLab
    
    # Order details
    p.drawString(100, 650, "Place Order Date: {}".format(order.created_at.strftime("%Y-%m-%d %H:%M:%S")))
    
    # Customer information
    p.drawString(100, 630, "Customer Name: {} {}".format(order.fname, order.lname))
    p.drawString(100, 610, "Email: {}".format(order.email))
    p.drawString(100, 590, "Phone: {}".format(order.phone))
    p.drawString(100, 570, "Address: {}".format(order.address))
    p.drawString(100, 550, "City: {}".format(order.city))
    p.drawString(100, 530, "State: {}".format(order.state))
    p.drawString(100, 510, "Pincode: {}".format(order.pincode))
    
    # Product details in table format
    data = [["Product Name", "Quantity", "Price", "Total Price"]]
    total_order_price = 0
    for item in order.orderitem_set.all():
        total_item_price = item.quantity * item.price
        data.append([item.product.p_name, item.quantity, "Rs.{}".format(item.price), "Rs.{}".format(total_item_price)])   
        
    column_widths = [180, 120, 120, 100]

    # Create the table
    table = Table(data, colWidths=column_widths)
    table.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 12),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.lightcyan),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                               ('GRID', (0, 0), (-1, -1), 1, colors.white)]))
    
    table.wrapOn(p, width, height)
    table_height = table._height
    table.drawOn(p, 70, height - 350 - table_height)  # Adjust the vertical position
    
    # Payment information
    p.drawString(100, 320, "Total Price: Rs.{}".format(order.total_price))
    p.drawString(100, 300, "Payment Mode: {}".format(order.payment_mode))
    p.drawString(100, 280, "Payment Status: {}".format("Paid" if OrderItem.payment_status else "Unpaid"))
    
  # Order status
    p.drawString(100, 260, "Order Status: {}".format(order.status))
    
    # Save canvas state before drawing footer
    p.saveState()
    footer(p, order)
    p.restoreState()
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

@login_required(login_url='login')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    invoice_pdf = generate_invoice_pdf(order)
    
    response = HttpResponse(invoice_pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_{}.pdf"'.format(order_id)
    return response
