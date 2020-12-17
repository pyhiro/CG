from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView, PasswordChangeView,
                                       PasswordChangeDoneView)
from django.http.response import JsonResponse
from .forms import (LoginForm, SignUpForm, UserSearchForm, UserUpdateForm,
                    SuperUserUpdateForm, SuperPointForm, PasswordForgetForm,
                    PointForm, UserSettingsForm, GradesPointForm)
from .models import User, Secret, Message, Goods, Grades, MessageCount, Test
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import datetime
import hashlib
import json
import os
import random
import smtplib
import ssl
import string
from email.mime.text import MIMEText
import urllib

import base58
import qrcode
import requests
import yaml

from . import wallet


class Login(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/home')
        return render(request, self.template_name, {'form': self.form_class})


class Logout(LoginRequiredMixin, LogoutView):
    template_name = 'login.html'


class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('password_change_done')
    template_name = 'change.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_name"] = "password_change"
        return context


class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView):
    def get(self, request, *args, **kwargs):
        user = self.request.user
        user.login_flag = True
        user.save()
        if user.is_superuser and not user.blockchain_address:
            w = wallet.Wallet()
            user.blockchain_address = 'Chain Gift'
            user.save()
            hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
            s = Secret(id_hash=hashed_id, public_key=w.public_key, private_key=w.private_key)
            s.save()
        return render(request, 'password_change_done.html')
    template_name = 'password_change_done.html'


def top(request):
    return render(request, 'top.html')


def create_transaction(request):
    json_data = json.loads(request.body)
    required = (
        'sender_private_key',
        'sender_blockchain_address',
        'recipient_blockchain_address',
        'sender_public_key',
        'value')
    if not all(k in json_data for k in required):
        return HttpResponse('missing values', status=400)

    sender_private_key = json_data['sender_private_key']
    sender_public_key = json_data['sender_public_key']
    sender_blockchain_address = json_data['sender_blockchain_address']
    recipient_blockchain_address = json_data['recipient_blockchain_address']
    value = int(json_data['value'])

    response = post_transaction(sender_private_key, sender_public_key,
                                sender_blockchain_address, recipient_blockchain_address,
                                value)

    if response.status_code == 201:
        return JsonResponse({'message': 'success'}, status=200)

    return JsonResponse({'message': 'fail', 'response': response}, status=400)


def point_send(request, pk):
    if not request.user.is_authenticated:
        return redirect(f'/login?next=/point_send/{pk}')
    user = request.user
    if user.student_id == pk:
        return redirect(f'/profile/{pk}')
    try:
        to_user = User.objects.get(student_id=pk, delete_flag=False)
    except:
        return HttpResponse('user not found')

    if request.method == 'GET':
        form = PointForm(initial={'point': user.template_point,
                                  'contents': 'ありがとう'})
        name = to_user.username
        params = {'name': name,
                  'form': form}
        return render(request, 'send.html', params)
    form = PointForm(request.POST)
    if not form.data['point'].isdigit() or int(form.data['point']) <= 0:
        return redirect(f'/point_send/{pk}')
    point = int(form.data['point'])
    msg = form.data['contents']
    hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
    secret = Secret.objects.get(id_hash=hashed_id)

    sender_private_key = secret.private_key
    sender_blockchain_address = user.blockchain_address
    recipient_blockchain_address = to_user.blockchain_address
    sender_public_key = secret.public_key
    value = int(point)

    response = post_transaction(sender_private_key, sender_public_key,
                                sender_blockchain_address, recipient_blockchain_address,
                                value)
    if response.status_code == 201:
        Message(contents=msg, sender=user.student_id,
                recipient=to_user.student_id, point=point).save()
        msg_count = MessageCount(from_grade_id=user.grade_id, from_class_id=user.class_id,
                                 to_grade_id=to_user.grade_id, to_class_id=to_user.class_id)
        msg_count.save()
        return redirect(f'/profile/{pk}')
    return JsonResponse({'message': 'fail', 'response': response}, status=400)


@login_required
def user_search(request):
    if not request.user.login_flag:
        return redirect('/change?next=/user_search')
    if request.method == 'POST':
        grade_id = request.POST.get('grade_id', None)
        class_id = request.POST.get('class_id', None)
        if grade_id and not class_id:
            users = User.objects.filter(grade_id=grade_id, delete_flag=False).exclude(is_superuser=True) \
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        elif grade_id and class_id:
            users = User.objects.filter(
                grade_id=grade_id, class_id=class_id, delete_flag=False).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        elif not grade_id and class_id:
            users = User.objects.filter(class_id=class_id, delete_flag=False).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'user_search.html', params)
        else:
            form = UserSearchForm(initial={'grade_id': ''})
            users = User.objects.exclude(delete_flag=True).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None, 'form': form}
            return render(request, 'user_search.html', params)

    form = UserSearchForm(initial={'grade_id': ''})
    users = User.objects.exclude(delete_flag=True).exclude(is_superuser=True)\
        .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
        .order_by('my_grade_id', 'my_class_id', 'furigana')
    params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None, 'form': form}
    return render(request, 'user_search.html', params)


@login_required
def home(request):
    user = request.user
    if not user.login_flag:
        return redirect('/change?next=/home')
    not_notified_messages = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count = len(not_notified_messages)
    my_blockchain_address = user.blockchain_address
    response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total = response.json()['amount']
    else:
        total = 'error'
    params = {'not_notified_message_count': not_notified_message_count,
              'total': total}
    return render(request, 'home.html', params)


@login_required
def message(request):
    user = request.user
    if not user.login_flag:
        return redirect('/change?next=/message')
    student_id = user.student_id
    try:
        Message.objects.filter(notify_flag=0, recipient=request.user.student_id).update(notify_flag=1)
    except:
        pass
    try:
        received_messages = Message.objects.filter(recipient=student_id, recipient_delete_flag=False).order_by('-id')
    except:
        received_messages = None
    try:
        send_messages = Message.objects.filter(sender=student_id, sender_delete_flag=False).order_by('-time_of_message')
    except:
        send_messages = None
    if received_messages:
        for obj in received_messages:
            sender_id = obj.sender
            try:
                sender_obj = User.objects.get(student_id=sender_id)
            except:
                continue
            if sender_obj.is_superuser:
                obj.sender = ('Chain Gift', sender_obj.student_id)
            else:
                obj.sender = (sender_obj.username, sender_id)
    if send_messages:
        for obj in send_messages:
            recipient_id = obj.recipient
            try:
                recipient_name = User.objects.get(student_id=recipient_id)
            except:
                continue
            obj.recipient = (recipient_name.username, recipient_id)

    params = {'receive': received_messages,
              'send': send_messages}
    return render(request, 'message.html', params)


@login_required
def message_detail(request, pk):
    msg = Message.objects.get(id=pk)
    user = request.user
    if not user.login_flag:
        return redirect(f'/change?next=/message_detail/{pk}')

    if msg.sender != user.student_id and msg.recipient != user.student_id:
        return redirect('/message')
    if msg.recipient == user.student_id and not msg.read_flag:
        msg.read_flag = True
        msg.save()

    if msg.recipient == user.student_id and msg.recipient_delete_flag:
        return HttpResponse('none')
    if msg.sender == user.student_id and msg.sender_delete_flag:
        return HttpResponse('none')

    my_user = User.objects.get(student_id=user.student_id)
    sender_id = msg.sender
    recipient_id = msg.recipient
    if sender_id == recipient_id:
        msg.sender = my_user.username
        msg.recipient = my_user.username
    elif sender_id == my_user.student_id:
        msg.sender = my_user.username
        recipient = User.objects.get(student_id=recipient_id)
        msg.recipient = recipient.username
    else:
        sender = User.objects.get(student_id=sender_id)
        msg.sender = sender.username
        msg.recipient = my_user.username
    send_user = User.objects.get(student_id=sender_id)
    receive_user = User.objects.get(student_id=recipient_id)
    if send_user.is_superuser:
        msg.sender = 'Chain Gift'
    if receive_user.is_superuser:
        msg.recipient = 'Chain Gift'
    # return render(request, 'message_detail.html', {'message': msg})
    time_lug = datetime.timedelta(hours=9)
    now = msg.time_of_message + time_lug
    now_str = now.strftime('%Y-%m-%d %H:%M')
    return JsonResponse({'sender': msg.sender,
                         'recipient': msg.recipient,
                         'contents': msg.contents,
                         'point': msg.point,
                         'time': now_str})


@login_required
def grades_super_point(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        users = User.objects.exclude(delete_flag=True)
        user_address = list(map(lambda u: u.blockchain_address, users))
        form = SuperPointForm(request.POST)
        point = form.data['point']
        if not point.isdigit():
            redirect('/super_point')
        if int(point) < 0:
            redirect('/super_point')
        point = int(point)
        msg = form.data['contents']
        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.get(id_hash=hashed_id)

        sender_private_key = secret.private_key
        sender_blockchain_address = user.blockchain_address
        recipient_blockchain_address = user_address
        sender_public_key = secret.public_key
        value = int(point)

        transaction = wallet.Transaction(
            sender_private_key,
            sender_public_key,
            sender_blockchain_address,
            str(recipient_blockchain_address.sort()),
            value)

        json_data_send = {
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'sender_public_key': sender_public_key,
            'value': value,
            'signature': transaction.generate_signature(),
        }

        response = requests.post(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions_super'),
            json=json_data_send, timeout=10)

        if response.status_code == 201:
            for usr in users:
                Message(contents=msg, sender=user.student_id,
                        recipient=usr.student_id, point=point).save()
        return redirect('/home')
    form = SuperPointForm()
    return render(request, 'super_point.html', {'form': form})


@login_required
def super_point(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        users = User.objects.exclude(delete_flag=True)
        user_address = list(map(lambda u: u.blockchain_address, users))
        form = SuperPointForm(request.POST)
        point = form.data['point']
        if not point.isdigit():
            redirect('/super_point')
        if int(point) < 0:
            redirect('/super_point')
        point = int(point)
        msg = form.data['contents']
        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.get(id_hash=hashed_id)

        sender_private_key = secret.private_key
        sender_blockchain_address = user.blockchain_address
        recipient_blockchain_address = user_address
        sender_public_key = secret.public_key
        value = int(point)

        transaction = wallet.Transaction(
            sender_private_key,
            sender_public_key,
            sender_blockchain_address,
            str(recipient_blockchain_address.sort()),
            value)

        json_data_send = {
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'sender_public_key': sender_public_key,
            'value': value,
            'signature': transaction.generate_signature(),
        }

        response = requests.post(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions_super'),
            json=json_data_send, timeout=10)

        if response.status_code == 201:
            for usr in users:
                Message(contents=msg, sender=user.student_id,
                        recipient=usr.student_id, point=point).save()
        return redirect('/home')
    form = SuperPointForm()
    return render(request, 'super_point.html', {'form': form})


@login_required
def point(request):
    user = request.user
    if not user.login_flag:
        return redirect('/change?next=/point')

    my_blockchain_address = user.blockchain_address
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
                try:
                    transacted_blockchain_address = transaction['transacted_blockchain_address']
                except:
                    continue
                try:
                    usr = User.objects.filter(blockchain_address=transacted_blockchain_address)[0]
                    if usr.is_superuser:
                        transaction['name'] = 'Chain Gift'
                    else:
                        transaction['name'] = usr
                except:
                    transaction['name'] = 'Miner'
                transaction['transacted_time'] = datetime.datetime.fromtimestamp(transaction['transacted_time'])
        if params['send']:
            for transaction in params['send']:
                try:
                    transacted_blockchain_address = transaction['transacted_blockchain_address']
                except:
                    continue
                try:
                    if transacted_blockchain_address == 'Chain Gift':
                        transaction['name'] = 'Chain Gift'
                    else:
                        usr = User.objects.get(blockchain_address=transacted_blockchain_address)
                        transaction['name'] = usr
                except:
                    transaction['name'] = 'Miner'
                transaction['transacted_time'] = datetime.datetime.fromtimestamp(transaction['transacted_time'])
                if user.is_superuser:
                    params['receive'][-1]['name'] = 'first point'

        return render(request, 'point.html', params, status=200)
    return JsonResponse({'message': 'fail', 'error': response.content}, status=400)


@login_required
def profile(request, pk=None):
    user = request.user
    if not user.login_flag:
        return redirect(f'/change?next=profile/{pk}')
    img_url = user.profile_img
    user = get_object_or_404(User, student_id=pk, delete_flag=False)
    if user.is_superuser and not request.user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        to_send = user.blockchain_address
        my_blockchain_address = request.user.blockchain_address
        if not to_send:
            return redirect(f'/profile/{pk}')
        form_data = PointForm(request.POST)
        if not form_data.is_valid():
            return HttpResponse('error')
        message = form_data.data['contents']

        if not message:
            return HttpResponse('message none')
        value = str(form_data.data['point'])

        if not value.isdigit() or int(value) <= 0:
            return redirect(f'/super_point')

        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.get(id_hash=hashed_id)
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
            if message:
                message_obj = Message(contents=message, sender=request.user.student_id,
                                      recipient=user.student_id, point=value)
                message_obj.save()
                msg_count = MessageCount(from_grade_id=user.grade_id, from_class_id=user.class_id,
                                         to_grade_id=user.grade_id, to_class_id=user.class_id)
                msg_count.save()
            return redirect(f'/profile/{pk}')
        else:
            return redirect('/home/')
    params = {
        'username': user.username,
        'grade_id': user.grade_id,
        'class_id': user.class_id,
        'img_url': user.profile_img
    }
    if user.birthday:
        birthday = user.birthday
        params['birthday'] = birthday
    if user.profile_message:
        user_profile = user.profile_message
        params['profile'] = user_profile

    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            if user.student_id == pk:
                params['self_user'] = True
        else:
            params['self_user'] = False
    params['user_img'] = img_url
    form = PointForm()
    params['form'] = form
    return render(request, 'profile.html', params)


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
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
                                   'birthday': user.birthday,
                                   'profile_message': user.profile_message})
    return render(request, 'edit_profile.html', {'form': form})


def shop_home(request):
    data = Goods.objects.all()
    return render(request, 'shop.html', {'data': data})


@login_required
def signup(request):
    # user = request.user
    # if not user.is_superuser:
    #     return request('/home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        data = form.data
        password_by_list = [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
        password = ''.join(password_by_list)

        b58str = base58.b58encode(password.encode()).decode('utf-8')
        password = b58str[:8]

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
        qr_img_name = make_qr(user.student_id)
        user.qr_img = qr_img_name
        user.save()

        send_gmail(password, data['email'])

        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        s = Secret(id_hash=hashed_id, public_key=w.public_key, private_key=w.private_key)
        s.save()
        return redirect('/signup')

    form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def goods_db(request):
    # m = Message(contents='good morning', sender=request.user.student_id, recipient=request.user.student_id)
    # m.save()
    category = request.GET.get('category', None)
    if category:
        goods = Goods.objects.filter(category=category)
    else:
        goods = Goods.objects.all()
    goods_dict = {'goods': []}
    for value in goods:
        goods_dict['goods'].append({'goods_id': value.id,
                                    'goods_name': value.name,
                                    'goods_value': value.price,
                                    'goods_img': value.goods_img,
                                    'goods_category': value.category,
                                    'goods_show': value.show})
    return JsonResponse(goods_dict)


@login_required
def management(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')
    return render(request, 'management.html')


@login_required
def all_users(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')
    if not request.user.login_flag:
        return redirect('/change?next=/user_search')
    if request.method == 'POST':
        grade_id = request.POST.get('grade_id', None)
        class_id = request.POST.get('class_id', None)
        if grade_id and not class_id:
            users = User.objects.filter(grade_id=grade_id, delete_flag=False)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'all_user.html', params)
        elif grade_id and class_id:
            users = User.objects.filter(grade_id=grade_id, class_id=class_id)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'all_user.html', params)
        elif not grade_id and class_id:
            users = User.objects.filter(class_id=class_id)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form}
            return render(request, 'all_user.html', params)
        else:
            form = UserSearchForm(initial={'grade_id': ''})
            users = User.objects.all()\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None,'form': form}
            return render(request, 'all_user.html', params)

    form = UserSearchForm(initial={'grade_id': ''})
    users = User.objects.all()\
        .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'}) \
        .order_by('my_grade_id', 'my_class_id', 'furigana')
    params = {'users': users, 'selected_grade_id': None, 'selected_class_id': None, 'form': form}
    return render(request, 'all_user.html', params)


@login_required()
def super_edit(request, pk):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')
    user = get_object_or_404(User, student_id=pk)
    
    if request.method == 'POST':
        form = SuperUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(f'/all_users/')
        params = {'form': form, 'message': '値が不正です'}
        return render(request, 'super_edit.html', params)

    form = SuperUserUpdateForm(initial={'grade_id': user.grade_id,                               'class_id': user.class_id,
                                        'email': user.email,
                                        'username': user.username,
                                        'furigana': user.furigana,
                                        'student_id': user.student_id,
                                        'delete_flag': user.delete_flag})

    return render(request, 'super_edit.html', {'form': form})


@login_required
def super_delete(request, pk):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')
    user = get_object_or_404(User, student_id=pk)
    user.delete_flag = True
    user.save()
    return redirect('/all_users')


@login_required
def get_ranking(request):
    if not request.user.login_flag:
        return redirect('/change?next=/ranking')

    now = datetime.datetime.now()
    month_first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_time_stamp = month_first.timestamp()

    response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'ranking'),
        {'duration': first_time_stamp},
        timeout=10)
    if response.status_code == 200:
        tmp_rank = response.json()[0]['ranking']
        receive_ranking, send_ranking = dict(), dict()

        for k, v in tmp_rank['receive_ranking'].items():
            user = User.objects.get(blockchain_address=k)
            receive_ranking[user.username] = v

        for k, v in tmp_rank['send_ranking'].items():
            user = User.objects.get(blockchain_address=k)
            send_ranking[user.username] = v

        sorted_send_ranking = sorted(send_ranking.items(), key=lambda x: x[1], reverse=True)
        sorted_receive_ranking = sorted(receive_ranking.items(), key=lambda x: x[1], reverse=True)
        params = {'send_ranking': sorted_send_ranking,
                  'receive_ranking': sorted_receive_ranking}
        return render(request, 'ranking.html', params)


@login_required
def grades(request):
    user = request.user
    if not user.login_flag:
        return redirect('/change?next=/grades')
    my_grades = Grades.objects.filter(student_id=user.student_id).order_by('-year', '-semester')
    return render(request, 'grades.html', {'my_grades': my_grades})


def forget_password(request):
    if request.method == 'POST':
        form = PasswordForgetForm(request.POST)
        email = form.data['email']
        user = get_object_or_404(User, email=email)
        random_query = [random.choice(string.ascii_letters + string.digits) for _ in range(30)]
        random_query_str = ''.join(random_query)
        user.password_change_query = random_query_str
        user.save()
        send_gmail(email=user.email, query=random_query_str)
        return redirect('/login')
    form = PasswordForgetForm()
    return render(request, 'forget.html', {'form': form})


def forget_change_password(request):
    query = request.GET.get('rand_query')
    email = request.GET.get('email')
    user = get_object_or_404(User, email=email)
    if user.password_change_query != query:
        return redirect('/')
    if user.is_authenticated:
        logout(request)
    password_list = [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
    password = ''.join(password_list)

    b58str = base58.b58encode(password.encode()).decode('utf-8')
    password = b58str[:8]

    user.set_password(password)
    user.password_change_query = None
    user.login_flag = False
    user.save()
    send_gmail(password=password, email=user.email, subject='パスワード更新')
    user = authenticate(request=request, email=email, password=password)
    login(request, user)
    return redirect('/')


@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        form = UserSettingsForm(request.POST)
        try:
            if form.data['dark_mode'] == 'on':
                user.dark_mode = True
        except MultiValueDictKeyError:
            user.dark_mode = False
        user.template_point = form.data['template_point']
        user.save()

    if user.dark_mode:
        form = UserSettingsForm(initial={'dark_mode': True, 'template_point': user.template_point})
    else:
        form = UserSettingsForm(initial={'dark_mode': False, 'template_point': user.template_point})
    params = {"form": form}
    return render(request, 'settings.html', params)


def grades_top(request):
    test_list = Test.objects.all().order_by('-year', '-semester', '-id')
    page_obj = paginate_queryset(request, test_list, 40)
    params = {
        'test_list': page_obj.object_list,
        'page_obj': page_obj,
    }
    return render(request, 'grades_top.html', params)


def paginate_queryset(request, queryset, count):
    paginator = Paginator(queryset, count)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj


def send_gmail(password=None, email=None, query=None, subject='初回ログイン'):
    with open('chain_gift/config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    gmail_account = config['account'][0]
    gmail_password = config['password'][0]
    mail_to = email

    body = password
    if query:
        subject = 'パスワード再発行'
        contents = f'http://127.0.0.1:8000/forget_change?rand_query={query}&email={email}'
        body = contents
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["To"] = mail_to
    msg["From"] = gmail_account

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=ssl.create_default_context())
    server.login(gmail_account, gmail_password)
    server.send_message(msg)


def make_qr(student_id):
    qr = f'http://127.0.0.1:8000/point_send/{student_id}'
    file_name = f"media/{student_id}.png"

    img = qrcode.make(qr)
    img.save(file_name)
    return f'{student_id}.png'


def post_transaction(sender_private_key, sender_public_key, sender_blockchain_address,
                     recipient_blockchain_address, value):
    transaction = wallet.Transaction(
        sender_private_key,
        sender_public_key,
        sender_blockchain_address,
        recipient_blockchain_address,
        value)

    json_data_send = {
        'sender_blockchain_address': sender_blockchain_address,
        'recipient_blockchain_address': recipient_blockchain_address,
        'sender_public_key': sender_public_key,
        'value': value,
        'signature': transaction.generate_signature(),
    }

    response = requests.post(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions'),
        json=json_data_send, timeout=10)
    return response
