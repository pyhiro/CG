from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import(LoginView, LogoutView)
from django.http.response import JsonResponse
from .forms import LoginForm, SignUpForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import json
import requests
import urllib

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


def shop_home(request):
    return render(request, 'shop.html')


def signup(request):
    if request.method == 'GET':
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        data = form.data
        print(data)
        ###########################TODO
        return redirect('/home/')

    form = SignUpForm()

    context = {'form':form}
    return render(request, 'polls/signup.html', context)