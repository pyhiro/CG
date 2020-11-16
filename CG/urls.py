"""CG URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from chain_gift import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/',views.home, name='home'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('change/', views.change, name='change'),
    path('message/', views.message, name='message'),
    path('point/', views.point, name='point'),
    path('user_search/', views.user_search, name='user_search'),
    path('wallet/amount/', views.calculate_amount, name='calculate_amount'),
    path('index', views.index, name='index'),
    path('wallet/', views.create_wallet, name='create_wallet'),
    path('transaction/', views.create_transaction, name='transaction'),
    path('shop/', views.shop_home, name='shop_home'),
    path('signup/', views.signup, name='signup'),
]
