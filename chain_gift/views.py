from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import(LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView)
from django.http.response import JsonResponse
from .forms import LoginForm, SignUpForm, UserSearchForm, UserUpdateForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import User, Secret, Message, Goods
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.core import serializers

import datetime
import hashlib
import json
import os
import random
import string
import smtplib, ssl
from email.mime.text import MIMEText
import urllib

import requests
import yaml

from . import wallet

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = 'login.html'


class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    """パスワード変更ビュー"""
    success_url = reverse_lazy('password_change_done')
    template_name = 'change.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # 継承元のメソッドCALL
        context["form_name"] = "password_change"
        return context


class PasswordChangeDone(LoginRequiredMixin,PasswordChangeDoneView):
    """パスワード変更完了"""
    template_name = 'password_change_done.html'


def index(request):
    return render(request, 'index.html')


@csrf_exempt
def create_wallet(request):
    if request.method == 'POST':
        my_wallet = wallet.Wallet()
        response = {
            'private_key': my_wallet.private_key,
            'public_key': my_wallet.public_key,
            'blockchain_address': my_wallet.blockchain_address,
        }
        return JsonResponse(response, status=200)


@login_required
@csrf_exempt
def user_info(request):
    if request.method == 'POST':
        user = request.user
        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.filter(id_hash=hashed_id)[0]
        response = {
            'private_key': secret.private_key,
            'public_key': secret.public_key,
            'blockchain_address': user.blockchain_address
        }
        return JsonResponse(response, status=200)

@csrf_exempt
def create_transaction(request):
    json_data = json.loads(request.body)

    required = (
        'sender_private_key',
        'sender_blockchain_address',
        'recipient_blockchain_address',
        'sender_public_key',
        'value')
    if not all(k in json_data for k in required):
        return 'missing values', 400

    sender_private_key = json_data['sender_private_key']
    sender_blockchain_address = json_data['sender_blockchain_address']
    recipient_blockchain_address = json_data['recipient_blockchain_address']
    sender_public_key = json_data['sender_public_key']
    value = int(json_data['value'])

    transaction = wallet.Transaction(
        sender_private_key,
        sender_public_key,
        sender_blockchain_address,
        recipient_blockchain_address,
        value)

    json_data_return = {
        'sender_blockchain_address': sender_blockchain_address,
        'recipient_blockchain_address': recipient_blockchain_address,
        'sender_public_key': sender_public_key,
        'value': value,
        'signature': transaction.generate_signature(),
    }

    response = requests.post(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions'),
        json=json_data_return, timeout=10)

    if response.status_code == 201:
        return JsonResponse({'message': 'success'}, status=200)
    return JsonResponse({'message': 'fail', 'response': response}, status=400)


def user_search(request):
    if request.method == 'GET':
        form = UserSearchForm()
        users = User.objects.all()
        params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None,'form': form}
        return render(request, 'user_search.html', params)

    if request.method == 'POST':

        grade_id = request.POST.get('grade_id', None)
        class_id = request.POST.get('class_id', None)
        if grade_id and not class_id:
            users = User.objects.filter(grade_id=grade_id)
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        elif grade_id and class_id:
            users = User.objects.filter(grade_id=grade_id, class_id=class_id)
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        elif not grade_id and class_id:
            users = User.objects.filter(class_id=class_id)
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        else:
            form = UserSearchForm()
            users = User.objects.all()
            params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None,'form': form}
            return render(request, 'user_search.html', params)


def home(request):

    return render(request, 'home.html')


def calculate_amount(request):
    if request.method == 'GET':
        my_blockchain_address = request.GET.get('blockchain_address', None)

        # json_data = json.loads(request.body)
        # if not all(k in json_data for k in required):

        if my_blockchain_address is None:
            return HttpResponse('Missing values', status=400)

        # my_blockchain_address = request.args.get('blockchain_address')
        response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
            {'blockchain_address': my_blockchain_address},
            timeout=10)
        if response.status_code == 200:
            total = response.json()['amount']
            return JsonResponse({'message': 'success', 'amount': total}, status=200)
        return JsonResponse({'message': 'fail', 'error': response.content}, status=400)


@login_required
def message(request):
    m = Message(contents='hello', sender='1902005', recipient='1902005')
    m.save()
    user = request.user
    student_id = user.student_id
    received_message = Message.objects.filter(recipient=student_id).order_by('-time_of_message')
    send_message = Message.objects.filter(sender=student_id).order_by('-time_of_message')
    params = {'receive': received_message,
              'send': send_message}
    return render(request, 'message.html', params)


def point(request):
    if request.method == 'GET':
        user = request.user
        my_blockchain_address = user.blockchain_address

        if my_blockchain_address is None:
            return HttpResponse('Missing values', status=400)

        response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'history'),
            {'blockchain_address': my_blockchain_address},
            timeout=10)
        if response.status_code == 200:
            history = response.json()['history']
            params = dict()
            params['send'] = history['send']
            params['receive'] = history['receive']
            if params['receive']:
                for transaction in params['receive']:
                    transaction['transacted_time'] = datetime.datetime.fromtimestamp(transaction['transacted_time'])
            if params['send']:
                for transaction in params['send']:
                    transaction['transacted_time'] = datetime.datetime.fromtimestamp(transaction['transacted_time'])

            return render(request, 'point.html', params, status=200)
        return JsonResponse({'message': 'fail', 'error': response.content}, status=400)


def profile(request, pk):
    user = User.objects.filter(student_id=pk)[0]
    if request.method == 'POST':
        to_send = user.blockchain_address
        my_blockchain_address = request.user.blockchain_address

        if not to_send:
            return render(request, 'home.html')
        message = request.POST.get('message')
        value = str(request.POST.get('amount'))
        if not value.isdigit():
            return render(request, 'home.html')

        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.filter(id_hash=hashed_id)[0]
        sender_private_key = secret.private_key
        sender_blockchain_address = my_blockchain_address
        recipient_blockchain_address = to_send
        sender_public_key = secret.public_key
        value = int(value)

        transaction = wallet.Transaction(
            sender_private_key,
            sender_public_key,
            sender_blockchain_address,
            recipient_blockchain_address,
            value)

        json_data_return = {
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'sender_public_key': sender_public_key,
            'value': value,
            'signature': transaction.generate_signature(),
        }

        response = requests.post(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions'),
            json=json_data_return, timeout=10)

        if response.status_code == 201:
            return redirect(f'/profile/{pk}')
        return JsonResponse({'message': 'fail', 'response': response}, status=400)

    params = {
        'username': user.username,
        'grade_id': user.grade_id,
        'class_id': user.class_id,
        'img_url': user.profile_img
    }
    if user.birth_day:
        birth_day = user.birth_day
        params['birth_day'] = birth_day
    if user.profile_message:
        user_profile = user.profile_message
        params['profile'] = user_profile

    if request.method == 'GET':
        user = request.user
        if int(user.pk) == pk:
            params['self_user'] = True
        else:
            params['self_user'] = False
    return render(request, 'profile.html', params)


@login_required
def edit_profile(request, pk):
    user = request.user
    if int(user.pk) != pk:
        return redirect('/home/')
    if request.method == 'POST':
        user = get_object_or_404(User, student_id=user.student_id)
        if user:
            before = user.profile_img
            form = UserUpdateForm(request.POST, request.FILES, instance=user)            
            if form.is_valid():
                form.save()
                user = get_object_or_404(User, student_id=user.student_id)
                after = user.profile_img
                if before and not after:
                    os.remove(f'media/{before}')
                if (before and after) and (before != after):
                    os.remove(f'media/{before}')
                return redirect(f'/profile/{user.pk}')
            params = {'form': form, 'message': '値が不正です'}
            return render(request, 'edit_profile.html', params)

    form = UserUpdateForm(initial={'profile_img': user.profile_img,
                                   'birth_day': user.birth_day,
                                   'profile_message': user.profile_message})
    return render(request, 'edit_profile.html', {'form': form})


def shop_home(request):
    data = Goods.objects.all()
    return render(request, 'shop.html', {'data': data})


def signup(request):
    if request.method == 'GET':
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        data = form.data
        password_by_list = [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
        password = ''.join(password_by_list)

        user = User(
            username=data['username'],
            email=data['email'],
            class_id=data['class_id'])
        user.set_password(password)
        user.furigana = data['furigana']
        user.student_id = data['student_id']
        user.grade_id = 1
        w = wallet.Wallet()
        user.blockchain_address = w.blockchain_address
        user.save()

        send_gmail(password, data['email'])

        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        s = Secret(id_hash=hashed_id, public_key=w.public_key, private_key=w.private_key)
        s.save()
        return redirect('/home/')

    form = SignUpForm()

    context = {'form': form}
    return render(request, 'polls/signup.html', context)


def goods_db(request):
    category = request.GET.get('category', None)
    if category:
        goods = Goods.objects.filter(category=category)
    else:
        goods = Goods.objects.all()
    return JsonResponse(serializers.serialize('json', goods), content_type="text/json-comment-filtered", safe=False)


def send_gmail(password, email):
    with open('chain_gift/config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    gmail_account = config['account'][0]
    gmail_password = config['password'][0]
    # メールの送信先★ --- (*2)
    mail_to = email

    # メールデータ(MIME)の作成 --- (*3)
    subject = "初回ログイン"
    body = password
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["To"] = mail_to
    msg["From"] = gmail_account

    # Gmailに接続 --- (*4)
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=ssl.create_default_context())
    server.login(gmail_account, gmail_password)
    server.send_message(msg)  # メールの送信
