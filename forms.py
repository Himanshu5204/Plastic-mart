# change password 
# forms.py 
from django import forms 
from django.contrib.auth.models import User 
from .models import ProductReview
 
 
class ChangePasswordForm(forms.Form): 
    #current_password = forms.CharField(label='Current Password', widget=forms.PasswordInput) 
    current_password = User.password 
    #forms.CharField(label='Current Password', widget=forms.PasswordInput) 
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput) 
    confirm_new_password = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput) 
 
    def clean(self): 
        cleaned_data = super().clean() 
        new_password = cleaned_data.get('new_password') 
        confirm_new_password = cleaned_data.get('confirm_new_password') 
 
        if new_password and confirm_new_password and new_password != confirm_new_password: 
            raise forms.ValidationError("The new passwords do not match.")
        
class ProductSearchForm(forms.Form):
    search_query = forms.CharField(label='Search Product')

class ProductReviewForm(forms.ModelForm): 
    class Meta: 
        model = ProductReview 
        fields = ['rating', 'review'] 
    def clean_rating(self): 
        rating = self.cleaned_data['rating'] 
        if rating < 1 or rating > 10: 
            raise forms.ValidationError("Rating must be between 1 and 10.") 
        return rating