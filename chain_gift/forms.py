from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import User, Message


class SuperPointForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('contents', 'point')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserSearchForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('grade_id', 'class_id')


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('profile_img', 'birth_day', 'profile_message')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class SuperUserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('grade_id', 'class_id', 'email', 'username', 'furigana', 'student_id', 'delete_flag')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('profile_img',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class PasswordForgetForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label   