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
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.top, name='top'),
    path('home/', views.home, name='home'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('change/', views.PasswordChange.as_view(), name='change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'), 
    path('message/', views.message, name='message'),
    path('point/', views.point, name='point'),
    path('user_search/', views.user_search, name='user_search'),
    path('index', views.index, name='index'),
    path('wallet/', views.create_wallet, name='create_wallet'),
    path('transaction/', views.create_transaction, name='transaction'),
    path('shop/', views.shop_home, name='shop_home'),
    path('signup/', views.signup, name='signup'),
    path('info/', views.user_info, name='info'),
    path('profile/<int:pk>', views.profile, name='profile'),
    path('profile/edit/<int:pk>', views.edit_profile, name='edit_profile'),
    path('goods_db/', views.goods_db, name='goods_db'),
    path('management/', views.management, name='management'),
    path('all_users/', views.all_users, name='all_users'),
    path('super_edit/<int:pk>', views.super_edit, name='super_edit'),
    path('super_delete/<int:pk>', views.super_delete, name='super_delete'),
    path('message_detail/<int:pk>', views.message_detail, name='message_detail'),
    path('quick_send/<int:pk>', views.quick_send, name='quick_send'),
    path('ranking/', views.get_ranking, name='ranking')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
