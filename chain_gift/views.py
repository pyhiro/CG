from django.shortcuts import render 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import(LoginView, LogoutView)
from .forms import LoginForm




class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = 'login.html'

def home(request):
  return render(request,'home.html')

def change(request):
  return render(request,'change.html')

def message(request):
  return render(request,'message.html')

def point(request):
  return render(request,'point.html')

def user_search(request):
  return render(request,'user_search.html')