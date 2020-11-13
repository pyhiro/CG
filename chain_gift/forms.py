from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import User


class LoginForm(AuthenticationForm):
    """ログオンフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label   


class SignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('student_id', 'class_id', 'username', 'furigana', 'email')

