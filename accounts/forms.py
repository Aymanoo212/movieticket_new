from django import forms
from .models import Account

class RegistrationForm(forms.ModelForm): # enregistrer un nouvel utilisateur.
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ['email', 'username', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class LoginForm(forms.Form): # pour connecter un utilisateur existant.
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)