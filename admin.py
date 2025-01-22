from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ExportActionMixin
from reportlab.pdfgen import canvas
from .admin import ExportActionMixin
from import_export import resources
from .mixins import ExportActionMixin
from datetime import datetime, timedelta
from django.urls import path
from django.shortcuts import redirect
from .reports import generate_report
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from import_export import resources

class signuser(admin.ModelAdmin):
    list_display=('fname','lname','email')

class CartAdmin(admin.ModelAdmin):
    list_display=('user','is_paid')
    
    def has_add_permission(self, request):
        return False

class CartItemAdmin(admin.ModelAdmin):
    list_display=('cart','product','quantity')

    def has_add_permission(self, request):
        return False

class OrderAdmin(admin.ModelAdmin):
    list_display = ('fname', 'lname', 'email', 'phone', 'address', 'total_price', 'payment_mode', 'payment_status', 'status', 'created_at')
    actions = ['generate_yearly_report', 'generate_monthly_report', 'generate_weekly_report']
    readonly_fields = ('fname', 'user','lname', 'email', 'phone','city','address', 'total_price','pincode','state', 'payment_mode', 'payment_status','payment_id', 'created_at')

    def payment_status(self, obj):
        # Access the related OrderItems and check if any of them have payment_status True
        return any(order_item.payment_status for order_item in obj.orderitem_set.all())

    # Define a boolean attribute for the admin column
    payment_status.boolean = True
    
    change_list_template = 'admin/list.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('generate_report/', self.admin_site.admin_view(self.generate_report), name='myapp_booking_generate_report'),
        ]
        return my_urls + urls

    def generate_report(self, request):
        if request.method == 'POST':
            date_range = request.POST.get('date_range')
            return generate_report(request, date_range)  # You need to define generate_report function
        else:
            return redirect(reverse('admin:myapp_booking_changelist'))

    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


            
            
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('fname', 'lname', 'email', 'subject', 'date', 'is_replied')
    list_filter = ('is_replied',)
    search_fields = ('fname', 'lname', 'email', 'subject', 'message')

    def is_replied(self, obj):
        # Check if there are any related InquiryReply objects for this inquiry
        return obj.replies.exists()

    # Set the admin column as boolean
    is_replied.boolean = True

    def has_add_permission(self, request):
        return False

class InquiryReplyAdmin(admin.ModelAdmin):
    list_display = ('inquiry_sender', 'sent_at', 'message')

    def inquiry_sender(self, obj):
        return f"{obj.inquiry.fname} {obj.inquiry.lname} - {obj.inquiry.email}"
    inquiry_sender.short_description = 'Inquiry Sender'

    def has_add_permission(self, request):
        return False

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('p_name', 'quantity', 'original_price', 'selling_price', 'created_at')

class ProductAdmin(admin.ModelAdmin, ExportActionMixin):
    list_display = ('p_name', 'quantity', 'original_price', 'selling_price', 'created_at')
    resource_class = ProductResource

    actions = ['export_as_pdf']

    def export_as_pdf(self, request, queryset):
        # Get products data
        products = queryset

        # Render template
        template = get_template('product_report.html')
        context = {'products': products}
        html = template.render(context)

        # Create PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="products_report.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    export_as_pdf.short_description = "Export selected products as PDF"

    # def get_shop_info():
    #    shop = Company.objects.first()
    #    return shop

class CustAdmin(admin.ModelAdmin):
    list_display = ('fname', 'lname', 'gender', 'address', 'email', 'phone', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit
            return self.readonly_fields + ('fname', 'lname', 'gender', 'address', 'email', 'phone', 'created_at','city','state','pincode','cust_id')
        return self.readonly_fields
    def has_add_permission(self, request):
        return False

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity', 'payment_status', 'is_canceled')
    list_filter = ('payment_status', 'is_canceled')
    search_fields = ('order__id', 'product__name')  # Assuming you have a 'name' field in the Product model
    readonly_fields = ('order', 'product','price', 'quantity')  # Set price and quantity fields as readonly

    def has_add_permission(self, request):
        return False

class CustomUserAdmin(UserAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return [field.name for field in self.model._meta.fields]  # Superusers can't edit any field
        else:
            return []  # Regular admins can edit all fields
        
class CartItemsAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_product_name', 'quantity')  # Displaying username, product name, and quantity
    readonly_fields = ('cart', 'product', 'quantity', 'get_user_name')  # Keeping other fields as readonly
    list_filter = ('cart__id',)  # Allowing filtering by cart__id

    def get_user_name(self, obj):
        return obj.cart.user.username if obj.cart.user else None

    get_user_name.short_description = 'User Name'

    def get_product_name(self, obj):
        return obj.product.p_name if obj.product else None

    get_product_name.short_description = 'Product Name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(cart__user=user)
        return qs

    def has_add_permission(self, request):
        return False  # Disallow adding new CartItems from the admin interface

    def has_change_permission(self, request, obj=None):
        return False  # Disallow changing existing CartItems from the admin interface

    def has_delete_permission(self, request, obj=None):
        return False  # Disallow deleting existing CartItems from the admin interface
    
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity', 'payment_status', 'is_canceled')
    readonly_fields = ('order', 'product','price', 'quantity')  # Set price and quantity fields as readonly

    def has_add_permission(self, request):
        return False

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')
    
# Register your models here.
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(cust,CustAdmin)
admin.site.register(Cart,CartAdmin)
admin.site.register(CartItems, CartItemsAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Inquiry,InquiryAdmin)
admin.site.register(InquiryReply, InquiryReplyAdmin)
admin.site.register(State)
admin.site.register(City)
admin.site.register(ProductReview)
admin.site.register(Company,CompanyAdmin)
#admin.site.register(signuser)

# admin.site.register(CartAdmin)
# admin.site.register(CartItemAdmin)
#admin.site.register(profile)
