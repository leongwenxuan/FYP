from django import forms
from .models import StaffProfile, Agency

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['agency', 'role', 'employee_id']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
        }