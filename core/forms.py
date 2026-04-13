from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, FoodListing


class RegistrationForm(forms.Form):
    """Multi-role registration form."""
    ROLE_CHOICES = [
        ('donor', 'Donor (Restaurant / Hotel)'),
        ('charity', 'Charity (NGO / Shelter)'),
    ]

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'id': 'reg-username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email address', 'id': 'reg-email'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password (min 8 chars)', 'id': 'reg-password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password', 'id': 'reg-password-confirm'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'id': 'reg-role'})
    )
    organization_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Organization name', 'id': 'reg-org'})
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'id': 'reg-phone'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Full address', 'rows': 2, 'id': 'reg-address'})
    )
    latitude = forms.FloatField(widget=forms.HiddenInput(attrs={'id': 'reg-lat'}), initial=12.9716)
    longitude = forms.FloatField(widget=forms.HiddenInput(attrs={'id': 'reg-lng'}), initial=77.5946)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError('Passwords do not match.')
        if User.objects.filter(username=cleaned.get('username')).exists():
            raise forms.ValidationError('Username already taken.')
        if User.objects.filter(email=cleaned.get('email')).exists():
            raise forms.ValidationError('Email already registered.')
        return cleaned


class LoginForm(forms.Form):
    """Simple email/username + password login."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'id': 'login-username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'id': 'login-password'})
    )


class FoodListingForm(forms.ModelForm):
    """Create a food surplus listing."""
    class Meta:
        model = FoodListing
        fields = ['food_type', 'description', 'quantity_kg', 'estimated_value', 'expiry_time', 'photo']
        widgets = {
            'food_type': forms.Select(attrs={'id': 'listing-food-type'}),
            'description': forms.Textarea(attrs={'placeholder': 'Describe the food...', 'rows': 3, 'id': 'listing-desc'}),
            'quantity_kg': forms.NumberInput(attrs={'placeholder': 'Quantity in kg', 'step': '0.5', 'min': '0.5', 'id': 'listing-qty'}),
            'estimated_value': forms.NumberInput(attrs={'placeholder': 'Estimated value (₹)', 'step': '10', 'min': '0', 'id': 'listing-value'}),
            'expiry_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'id': 'listing-expiry'}),
            'photo': forms.FileInput(attrs={'accept': 'image/*', 'id': 'listing-photo'}),
        }


class DeliveryPhotoForm(forms.Form):
    """Upload delivery confirmation photo."""
    photo = forms.ImageField(
        widget=forms.FileInput(attrs={'accept': 'image/*', 'id': 'delivery-photo'})
    )
