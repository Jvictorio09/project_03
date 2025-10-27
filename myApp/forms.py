from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Lead, PropertyUpload, Property


class LoginForm(AuthenticationForm):
    """Custom login form with better styling"""
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'you@company.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )


class LeadForm(forms.ModelForm):
    consent_contact = forms.BooleanField(required=False)

    class Meta:
        model = Lead
        fields = [
            "name",
            "phone",
            "email",
            "buy_or_rent",
            "budget_max",
            "beds",
            "areas",
            "consent_contact",
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        return phone.replace(" ", "").strip()


class PropertyUploadForm(forms.ModelForm):
    class Meta:
        model = PropertyUpload
        fields = ['title', 'description', 'price_amount', 'city', 'area', 'beds', 'baths', 'hero_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'e.g., Modern 2BR Downtown Condo with City Views'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Describe the property, its features, and what makes it special...'
            }),
            'price_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': '3500'
            }),
            'city': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }, choices=[
                ('', 'Select City'),
                ('Los Angeles', 'Los Angeles'),
                ('New York', 'New York'),
                ('Chicago', 'Chicago'),
                ('Miami', 'Miami'),
            ]),
            'area': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'e.g., Downtown, Hollywood, Manhattan'
            }),
            'beds': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': '2'
            }),
            'baths': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': '2'
            }),
            'hero_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hero_image'].required = True


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
                'class': 'form-control',
                'placeholder': 'Property title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Property description'
            }),
            'price_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price in PHP'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area/Neighborhood'
            }),
            'beds': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'baths': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'floor_area_sqm': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'parking': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'hero_image': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image URL'
            }),
            'badges': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated badges'
            }),
            'affiliate_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Source'
            }),
            'commissionable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


