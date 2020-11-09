from django.shortcuts import render #htmlを返すやつ

# Create your views here.
def home(request):
  return render(request,'home.html')

def login(request):
  return render(request, 'login.html')