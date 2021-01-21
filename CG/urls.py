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
    path('transaction/', views.create_transaction, name='transaction'),
    path('shop/', views.shop_home, name='shop_home'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:pk>/', views.profile, name='profile'),
    path('goods_db/', views.goods_db, name='goods_db'),
    path('management/', views.management, name='management'),
    path('all_users/', views.all_users, name='all_users'),
    path('super_edit/<str:pk>', views.super_edit, name='super_edit'),
    path('super_delete/<str:pk>', views.super_delete, name='super_delete'),
    path('message_detail/<int:pk>', views.message_detail, name='message_detail'),
    path('point_send/<str:pk>', views.point_send, name='point_send'),
    path('ranking/', views.get_ranking, name='ranking'),
    path('forget/', views.forget_password, name='forget'),
    path('forget_change/', views.forget_change_password, name='forget_change'),
    path('grades/', views.grades, name='grades'),
    path('grades/edit/<int:pk>', views.grades_edit, name='grades_edit'),
    path('grades/super_point/<int:pk>', views.grades_super_point, name='super_point'),
    path('grades/top/', views.grades_top, name='grades_top'),
    path('grades/edit/', views.grades, name='grades'),
    path('test/create/', views.create_test, name='create_test'),
    path('settings/', views.settings, name='settings'),
    path('super_point/', views.super_point, name='super_point'),
    path('add_subject/<int:pk>', views.add_subject, name='super_point'),
    path('grades/result/<int:pk>/<str:order>', views.test_result_super, name='super_point'),
    path('return_csv/<int:pk>/<str:order>', views.return_csv, name='super_point'),
    path('test_delete/', views.test_delete, name='super_point'),
    path('deleted/', views.deleted, name='super_point'),
    path('to_deleted/', views.to_deleted, name='super_point'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
