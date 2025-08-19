from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ChickRequest, ChickStock

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'gender', 'nin_number', 'contact', 'recommender_name', 'recommender_nin']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 18, 'max': 30}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nin_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your NIN Number'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'recommender_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recommender Full Name'}),
            'recommender_nin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recommender NIN Number'}),
        }

class ChickRequestForm(forms.ModelForm):
    class Meta:
        model = ChickRequest
        fields = ['chick_type', 'breed_type', 'quantity_requested', 'farmer_type', 'notes']
        widgets = {
            'chick_type': forms.Select(attrs={'class': 'form-control'}),
            'breed_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'farmer_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
    
    def clean_quantity_requested(self):
        quantity = self.cleaned_data['quantity_requested']
        farmer_type = self.cleaned_data.get('farmer_type')
        
        if farmer_type == 'starter' and quantity > 100:
            raise forms.ValidationError("Starter farmers can only request up to 100 chicks")
        elif farmer_type == 'returning' and quantity > 500:
            raise forms.ValidationError("Returning farmers can only request up to 500 chicks")
        
        return quantity

class ChickStockForm(forms.ModelForm):
    class Meta:
        model = ChickStock
        fields = ['chick_type', 'quantity', 'age_in_days']
        widgets = {
            'chick_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'age_in_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
