from django import forms
from .models import Campaign, CampaignStep, Property, Lead, PropertyUpload

# Add this after the existing forms

class CampaignForm(forms.ModelForm):
    """Form for creating/editing campaigns"""
    
    class Meta:
        model = Campaign
        fields = ['name', 'type', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'e.g., New Listings Alert'
            }),
            'type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'style': 'color-scheme: dark;'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'style': 'color-scheme: dark;'
            }),
        }


class CampaignStepForm(forms.ModelForm):
    """Form for creating/editing campaign steps"""
    
    class Meta:
        model = CampaignStep
        fields = ['name', 'subject', 'body_template', 'delay_hours']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'e.g., Welcome Email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'e.g., Welcome to our property updates!'
            }),
            'body_template': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none',
                'rows': 8,
                'placeholder': 'Write your email template here. Use {{ lead.name }}, {{ lead.email }}, {{ organization.name }} for personalization.'
            }),
            'delay_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'min': '0',
                'placeholder': '0'
            }),
        }


# Restored legacy forms expected by views.py

class PropertyForm(forms.ModelForm):
    """Form for creating/editing properties"""
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'price_amount', 'city', 'area',
            'beds', 'baths', 'floor_area_sqm', 'parking', 'hero_image',
            'badges', 'affiliate_source', 'commissionable'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'e.g., Modern 2BR Downtown Condo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none',
                'rows': 4,
                'placeholder': 'Describe the property, its features, and location...'
            }),
            'price_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 pl-8 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': '0',
                'step': '1'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'City'
            }),
            'area': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'Area/Neighborhood'
            }),
            'beds': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'min': '0',
                'placeholder': '0'
            }),
            'baths': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'min': '0',
                'placeholder': '0'
            }),
            'floor_area_sqm': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'min': '0',
                'placeholder': '0',
                'step': '0.01'
            }),
            'parking': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-violet-600 bg-white/5 border-white/10 rounded focus:ring-violet-500 focus:ring-2'
            }),
            'hero_image': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'badges': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated badges'
            }),
            'affiliate_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Zillow, Realtor.com'
            }),
            'commissionable': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-violet-600 bg-white/5 border-white/10 rounded focus:ring-violet-500 focus:ring-2'
            }),
        }


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'buy_or_rent', 'budget_max', 'beds', 'areas']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'buy_or_rent': forms.Select(attrs={'class': 'form-control', 'style': 'color-scheme: dark;'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'beds': forms.NumberInput(attrs={'class': 'form-control'}),
            'areas': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PropertyUploadForm(forms.ModelForm):
    class Meta:
        model = PropertyUpload
        fields = ['title', 'description', 'price_amount', 'city', 'area', 'beds', 'baths', 'hero_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'beds': forms.NumberInput(attrs={'class': 'form-control'}),
            'baths': forms.NumberInput(attrs={'class': 'form-control'}),
            'hero_image': forms.URLInput(attrs={'class': 'form-control'}),
        }


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
