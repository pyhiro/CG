from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import(LoginView, LogoutView)
from django.http.response import JsonResponse
from .forms import LoginForm, SignUpForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import User, Secret

import hashlib
import json
import random
import requests
import string
import urllib

import smtplib, ssl
from email.mime.text import MIMEText

from . import wallet

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = 'login.html'


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


@csrf_exempt
def create_transaction(request):
    json_data = json.loads(request.body)
    print(json_data)

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


def home(request):

    return render(request, 'home.html')


def calculate_amount(request):
    if request.method == 'GET':
        # required = ['blockchain_address']
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


def change(request):
    return render(request, 'change.html')


def message(request):
    return render(request, 'message.html')


def point(request):

    return render(request, 'point.html')


def user_search(request):
    return render(request, 'user_search.html')


def profile(request):
    return render(request, 'profile.html')


def shop_home(request):
    return render(request, 'shop.html')


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


def send_gmail(password, email):
    gmail_account = "cgift1158@gmail.com"
    gmail_password = "chenpo1234"
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
    print("ok.")