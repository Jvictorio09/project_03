from django import forms
from .models import Lead, PropertyUpload


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


