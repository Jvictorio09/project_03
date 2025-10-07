from django import forms
from .models import Lead


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


