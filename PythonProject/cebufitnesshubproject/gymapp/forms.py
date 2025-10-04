from django import forms
from .models import MemberRegistration

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = MemberRegistration
        fields = '__all__'