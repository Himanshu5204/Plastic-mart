from django.db import models
from django.contrib.auth.models import User
import datetime
import os
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.mail import send_mail
from django.core.exceptions import ValidationError


# Create your models here.
# def get_file_path(request,filename):
#     original_filename=filename
#     nowTime=datetime.datetime.now().strftime('%Y%m%d%H:%M:%S')
#     filename="%s%s" % (nowTime.original_filename)
#     return os.path.join('uploads/',filename)

class State(models.Model):
    name=models.CharField(max_length=45,unique=True)

    class Mete:
        verbose_name='State'
        verbose_name_plural='State'

    def __str__(self):
        return self.name
    
class City(models.Model):
    name=models.CharField(max_length=45,unique=True)
    state=models.ForeignKey(State,on_delete=models.CASCADE)

    class Meta:
        verbose_name='City'
        verbose_name_plural='City'
    
    def __str__(self):
        return self.name



class Inquiry(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    fname=models.CharField(max_length=85)
    lname=models.CharField(max_length=85)
    email=models.EmailField()
    subject=models.CharField(max_length=200)
    message=models.TextField(max_length=200)
    date=models.DateTimeField(default=timezone.now)
    is_replied=models.BooleanField(default=False)

    class Meta:
        verbose_name='Inquiry'
        verbose_name_plural='Inquiry'
    
    def __str__(self):
        return f"Inquiry By - {self.fname} - {self.email}"

class InquiryReply(models.Model):
    inquiry=models.ForeignKey(Inquiry,on_delete=models.CASCADE,related_name="replies")
    message=models.TextField()
    sent_at=models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name='Response to Inquiry'
        verbose_name_plural='Response to Inquiry'

    def __str__(self):
        return f"Inquiry Reply - {self.inquiry.subject} - {self.sent_at}"

    def get_inquiry_email(self):
        return self.inquiry.email
    get_inquiry_email.short_description="Inquiry Email"

    def send_email(self):
        try:
            send_mail(
                subject='Reply to your inquiry',
                message=self.message,
                from_email='himanshidevani22@gmail.com',
                recipient_list=[self.inquiry.email],
                fail_silently=False
            )
        except Exception as e:
            print(f'An error occurred: {e}')

    def save(self,*args,**kwargs):
        if not self.pk:
            self.send_email()
            self.inquiry.is_replied=True
            self.inquiry.save()
        super().save(*args,**kwargs)


class profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE, related_name="profile")
    is_email_verified=models.BooleanField(default=False)
    email_token=models.CharField(max_length=100,null=True,blank=False)
    profile_image=models.ImageField(upload_to='profile')

    def get_cart_count(self):
        return CartItems.objects.filter(Cart.is_paid == False, Cart.user == self.user).count()

def get_file_path(instance,filename):
    return f"uploads/{filename}"

class Category(models.Model):
    category_slug = models.CharField(max_length=150,null=False,blank=False)
    c_name=models.CharField(max_length=20,null=False,blank=False)
    description=models.TextField(max_length=500,null=False,blank=False)
    status=models.BooleanField(default=False,help_text="0=default,1=Hidden")
    trending=models.BooleanField(default=False,help_text="0=default,1=Hidden")
    meta_title=models.CharField(max_length=150,null=False,blank=False)
    meta_keyword=models.CharField(max_length=150,null=False,blank=False)
    meta_description=models.TextField(max_length=500,null=False,blank=False)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.c_name}"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_slug = models.CharField(max_length=150, null=False, blank=False)
    p_name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    p_image = models.ImageField(upload_to=get_file_path, null=True, blank=True)
    small_description = models.CharField(max_length=250, null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    description = models.TextField(max_length=500, null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0=default,1=Hidden")
    trending = models.BooleanField(default=False, help_text="0=default,1=Hidden")
    tag = models.CharField(max_length=150, null=False, blank=False)
    meta_title = models.CharField(max_length=150, null=False, blank=False)
    meta_keyword = models.CharField(max_length=150, null=False, blank=False)
    meta_description = models.TextField(max_length=500, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.p_name

    class Meta:
        ordering = ['p_name']

    def clean(self):
        super().clean()
        if self.quantity < 10:
            raise ValidationError("Quantity should be at least 10.")

    # Add a constraint at the database level to ensure minimum quantity is 10 what about out of stock 
    def save(self, *args, **kwargs):
        if self.quantity < 10:
            raise ValidationError("Quantity should be at least 10.")
        super().save(*args, **kwargs)
        
class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    fname=models.CharField(max_length=150,null=False)
    lname=models.CharField(max_length=150,null=False)
    email=models.CharField(max_length=150,null=False)
    phone=models.CharField(max_length=150,null=False)
    address=models.TextField(null=False)
    city=models.CharField(max_length=150,null=False)
    state=models.CharField(max_length=150,null=False)
    pincode=models.CharField(max_length=150,null=False)
    total_price=models.FloatField(null=False)
    payment_mode=models.CharField(null=False, max_length=50)
    payment_id= models.CharField(max_length=250, null=True)
    orderstatuses=(
    ('Pending','Pending'),
    ('Out For Shipping','Out For Shipping'),
    ('Completed','Completed'),
    ('Cancelled','Cancelled'),
    ('Refund initialized','Refund initialized'),
    ('Refund successful','Refund successful'),
    )
    status=models.CharField(max_length=150,choices=orderstatuses,default='Pending')
    tracking_no=models.CharField(null=True, max_length=150)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.id,self.tracking_no)

class ProductReview(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews') 
    rating = models.IntegerField()  # Assuming rating is an integer field for simplicity 
    review = models.TextField() 
    posted_at = models.DateTimeField(auto_now_add=True) 
 
    def __str__(self): 
        return f"Review by {self.user.username} for {self.product.p_name}"
    
class Company(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    def str(self):
        return self.name

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    price=models.FloatField(null=False)
    quantity=models.IntegerField(null=False)
    payment_status=models.BooleanField(default=False)
    is_canceled=models.BooleanField(default=False)

    def __str__(self):
         return '{} - {}'.format(self.order.id, self.order.tracking_no)

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='carts')
    is_paid = models.BooleanField(default=False)
    # session_id = models.CharField(max_length=255, null=True, blank=True) for annonymous 

    def get_cart_total(self):
        cart_items=self.cart_items.all()
        price=[]
        for cart_item in cart_items:
            price.append(cart_item.product.selling_price)
        return sum(price)
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        else:
            return f"Anonymous Cart ({self.session_id})"
    
    
class CartItems(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE, related_name='cart_items')
    product=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True)
    quantity = models.IntegerField(default=1)
     
    def get_product_price(self):
        price=[self.product.selling_price]
        return sum(price)
    def sub_total(self):
        return self.product.selling_price*self.quantity
    
    def __unicode__(self):
        return self.product
    
    def __str__(self):
        return f"{self.quantity} x {self.product} ---->    {self.cart}"

class cust(models.Model):
    ch=[('Male','Male'),('Female','Female')]
    cust_id=models.ForeignKey(User,on_delete=models.CASCADE)
    state=models.ForeignKey(State,on_delete=models.CASCADE)
    email=models.CharField(max_length=150,null=False) 
    fname=models.CharField(max_length=50,default=None) 
    lname=models.CharField(max_length=50,default=None)  
    phone=models.CharField(max_length=50,default=None)
    gender=models.CharField(max_length=40,choices=ch,default='Male') 
    address=models.TextField(null=False, default='')
    city=models.CharField(max_length=150,null=True,default='',blank=True)
    state=models.CharField(max_length=150,null=True,default='')
    pincode=models.CharField(
        null=True,
        max_length=6,
        validators=[
            RegexValidator(
                regex='^[0-9]{6}$',
                message='Enter a valid 6 digit pincode',
                code='Invalid_pin_code'
            ),
        ]      
    )
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"{self.fname}"
