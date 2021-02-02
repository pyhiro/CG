from django.shortcuts import render, redirect, get_object_or_404
import re
from django.template.defaulttags import register
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView, PasswordChangeView,
                                       PasswordChangeDoneView)
from django.http.response import JsonResponse
from .forms import (LoginForm, SignUpForm, UserSearchForm, UserUpdateForm,
                    SuperUserUpdateForm, SuperPointForm, PasswordForgetForm,
                    PointForm, UserSettingsForm, GradesPointForm, CreateTestForm, TestSearchForm, MyPasswordChangeForm,
                    AddSubjectForm, GoodsRegisterForm)
from .models import User, Secret, Message, Goods, Grades, MessageCount, Test, TestSubject
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.http import HttpResponse, HttpRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from bisect import bisect
import datetime
import hashlib
import json
import os
import random
import smtplib
import ssl
import string
from typing import (List, Tuple, Union)
from email.mime.text import MIMEText
import urllib

import base58
import numpy as np
from PIL import Image
import qrcode
import requests
from requests.models import Response
import yaml

from . import wallet


class Login(LoginView):
    form_class = LoginForm
    template_name: str = 'login.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if self.request.user.is_authenticated:
            return redirect('/home')
        return render(request, self.template_name, {'form': self.form_class})


class Logout(LoginRequiredMixin, LogoutView):
    template_name: str = 'login.html'


class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('password_change_done')
    template_name = 'change.html'
    form_class = MyPasswordChangeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_name"] = "password_change"
        return context


class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        user: User = self.request.user
        user.login_flag = True
        user.save()
        if user.is_superuser and not user.blockchain_address:
            user.grade_id = '管理者'
            user.class_id = '管理者'
            user.save()
            w: wallet.Wallet = wallet.Wallet()
            user.blockchain_address: str = 'Chain Gift'
            user.save()
            hashed_id: str = hashlib.sha256(user.student_id.encode()).hexdigest()
            s: Secret = Secret(id_hash=hashed_id, public_key=w.public_key, private_key=w.private_key)
            s.save()
        return render(request, 'password_change_done.html')
    template_name: str = 'password_change_done.html'


def top(request: HttpRequest) -> HttpResponse:
    return render(request, 'top.html')


def deleted(request: HttpRequest) -> HttpResponse:
    return render(request, 'deleted.html')


def to_deleted(request: HttpRequest) -> HttpResponse:
    return render(request, 'todeleted.html')


def point_send(request: HttpRequest, pk: str) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(f'/login?next=/point_send/{pk}')
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')

    if user.student_id == pk:
        return redirect(f'/profile/{pk}')
    try:
        to_user: User = User.objects.get(student_id=pk, delete_flag=False)
    except:
        return HttpResponse('user not found')

    if request.method == 'GET':
        my_blockchain_address: str = user.blockchain_address
        response: Response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
            {'blockchain_address': my_blockchain_address},
            timeout=5)
        if response.status_code == 200:
            total: int = response.json()['amount']
        else:
            total: str = ''
        response: Response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'can_buy'),
            {'blockchain_address': my_blockchain_address},
            timeout=5)
        if response.status_code == 200:
            can_buy_total: int = response.json()['can_buy']
        else:
            can_buy_total: str = ''
        if total and can_buy_total:
            only_send = total - can_buy_total
        else:
            only_send = ''
        form = PointForm(initial={'point': user.template_point,
                                  'contents': 'ありがとう'})

        name: str = to_user.username
        params = {'name': name,
                  'form': form,
                  'total': total,
                  'only_send': only_send}
        return render(request, 'send.html', params)
    form = PointForm(request.POST)
    if not form.data['point'].isdigit() or int(form.data['point']) <= 0:
        return redirect(f'/point_send/{pk}')
    point: int = int(form.data['point'])
    msg: str = form.data['contents']
    hashed_id: str = hashlib.sha256(user.student_id.encode()).hexdigest()
    secret: Secret = Secret.objects.get(id_hash=hashed_id)

    sender_private_key: str = secret.private_key
    sender_blockchain_address: str = user.blockchain_address
    recipient_blockchain_address: str = to_user.blockchain_address
    sender_public_key: str = secret.public_key
    value: int = int(point)

    response: Response = post_transaction(sender_private_key, sender_public_key,
                                          sender_blockchain_address, recipient_blockchain_address,
                                          value)
    if response.status_code == 201:
        Message(contents=msg, sender=user.student_id,
                recipient=to_user.student_id, point=point).save()
        msg_count: MessageCount = MessageCount(from_grade_id=user.grade_id, from_class_id=user.class_id,
                                               to_grade_id=to_user.grade_id, to_class_id=to_user.class_id)
        msg_count.save()
        return redirect(f'/profile/{pk}')
    return JsonResponse({'message': 'fail', 'response': response}, status=400)


@login_required
def user_search(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect('/change?next=/user_search')

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)

    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''

    if request.method == 'POST':
        grade_id: str = request.POST.get('grade_id', None)
        class_id: str = request.POST.get('class_id', None)
        if grade_id and not class_id:
            users: QuerySet = User.objects.filter(grade_id=grade_id, delete_flag=False).exclude(is_superuser=True) \
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form, 'total': total,
                      'not_notified_message_count': not_notified_message_count}
            return render(request, 'user_search.html', params)
        elif grade_id and class_id:
            users: QuerySet = User.objects.filter(
                grade_id=grade_id, class_id=class_id, delete_flag=False).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form: UserSearchForm = UserSearchForm(request.POST)
            params = {'users': users, 'form': form, 'total': total,
                      'not_notified_message_count': not_notified_message_count}
            return render(request, 'user_search.html', params)
        elif not grade_id and class_id:
            users = User.objects.filter(class_id=class_id, delete_flag=False).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            form = UserSearchForm(request.POST)
            params = {'users': users, 'form': form, 'total': total,
                      'not_notified_message_count': not_notified_message_count}
            return render(request, 'user_search.html', params)
        else:
            form = UserSearchForm(initial={'grade_id': ''})
            users = User.objects.exclude(delete_flag=True).exclude(is_superuser=True)\
                .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
                .order_by('my_grade_id', 'my_class_id', 'furigana')
            params = {'users': users, 'form': form, 'total': total,
                      'not_notified_message_count': not_notified_message_count}
            return render(request, 'user_search.html', params)

    form = UserSearchForm(initial={'grade_id': ''})
    users: QuerySet = User.objects.exclude(delete_flag=True).exclude(is_superuser=True)\
        .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'})\
        .order_by('my_grade_id', 'my_class_id', 'furigana')
    params = {'users': users, 'selected_grade_id': None,
              'selected_class_id': None, 'form': form,
              'total': total, 'not_notified_message_count': not_notified_message_count}
    return render(request, 'user_search.html', params)


@login_required
def home(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect(f'/change?next=/home')
    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)
    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'can_buy'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        can_buy_total: int = response.json()['can_buy']
    else:
        can_buy_total: str = ''
    if user.is_superuser:
        not_notified_message_count = 0
    params = {'not_notified_message_count': not_notified_message_count,
              'total': total,
              'can_buy_total': can_buy_total}
    return render(request, 'home.html', params)


@login_required
def message(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect('/change?next=/message')
    student_id: str = user.student_id
    try:
        Message.objects.filter(notify_flag=0, recipient=request.user.student_id).update(notify_flag=1)
    except:
        pass
    try:
        received_messages: QuerySet = Message.objects.filter(recipient=student_id,
                                                             recipient_delete_flag=False).order_by('-id')
    except:
        received_messages: None = None
    try:
        send_messages: QuerySet = Message.objects.filter(sender=student_id,
                                                         sender_delete_flag=False).order_by('-time_of_message')
    except:
        send_messages: None = None
    if received_messages:
        for obj in received_messages:
            sender_id: str = obj.sender
            try:
                sender_obj: User = User.objects.get(student_id=sender_id)
            except:
                continue
            if sender_obj.is_superuser:
                obj.sender: Tuple[str, str] = ('Chain Gift', sender_obj.student_id)
            else:
                obj.sender = (sender_obj.username, sender_id)
    if send_messages:
        for obj in send_messages:
            recipient_id: str = obj.recipient
            try:
                recipient_user: User = User.objects.get(student_id=recipient_id)
            except:
                continue
            obj.recipient = (recipient_user.username, recipient_id)

    params = {'receive': received_messages,
              'send': send_messages}
    if user.is_superuser:
        params['receive'] = ''

    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    params['total'] = total
    return render(request, 'message.html', params)


@login_required
def message_detail(request: HttpResponse, pk: int) -> JsonResponse:
    msg: Message = Message.objects.get(id=pk)
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect(f'/change?next=/message_detail/{pk}')

    if msg.sender != user.student_id and msg.recipient != user.student_id:
        return redirect('/message')
    if msg.recipient == user.student_id and not msg.read_flag:
        msg.read_flag: bool = True
        msg.save()

    if msg.recipient == user.student_id and msg.recipient_delete_flag:
        return HttpResponse('none')
    if msg.sender == user.student_id and msg.sender_delete_flag:
        return HttpResponse('none')

    my_user: User = User.objects.get(student_id=user.student_id)
    sender_id: str = msg.sender
    recipient_id: str = msg.recipient
    if sender_id == recipient_id:
        msg.sender: str = my_user.username
        msg.recipient: str = my_user.username
    elif sender_id == my_user.student_id:
        msg.sender: str = my_user.username
        recipient: User = User.objects.get(student_id=recipient_id)
        msg.recipient: str = recipient.username
    else:
        sender: User = User.objects.get(student_id=sender_id)
        msg.sender: str = sender.username
        msg.recipient: str = my_user.username
    send_user = User.objects.get(student_id=sender_id)
    receive_user: User = User.objects.get(student_id=recipient_id)
    if send_user.is_superuser:
        msg.sender: str = 'Chain Gift'
    if receive_user.is_superuser:
        msg.recipient: str = 'Chain Gift'
    time_lug: datetime.timedelta = datetime.timedelta(hours=9)
    now: datetime.time = msg.time_of_message + time_lug
    now_str: str = now.strftime('%Y-%m-%d %H:%M')
    return JsonResponse({'sender': msg.sender,
                         'recipient': msg.recipient,
                         'contents': msg.contents,
                         'point': msg.point,
                         'time': now_str,
                         'recipient_delete_url': f'http://127.0.0.1:8000/message/delete/{msg.id}/recipient',
                         'sender_delete_url': f'http://127.0.0.1:8000/message/delete/{msg.id}/sender'})


@login_required
def message_delete(request, pk: int, sender_or_recipient: str) -> HttpResponse:
    msg: Message = Message.objects.get(id=pk)
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect(f'/change?next=/message_detail/{pk}')

    if sender_or_recipient == 'sender' and user.student_id == msg.sender:
        msg.sender_delete_flag: bool = True
        msg.save()
    elif sender_or_recipient == 'recipient' and user.student_id == msg.sender:
        msg.recipient_delete_flag: bool = True
        msg.save()
    return JsonResponse({'message_id': msg.id})


@login_required
def super_point(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if not user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        users: QuerySet = User.objects.exclude(delete_flag=True).exclude(is_superuser=True)
        user_address: List[str] = list(map(lambda u: u.blockchain_address, users))
        form: SuperPointForm = SuperPointForm(request.POST)
        point: str = form.data['point']
        if not point.isdigit():
            redirect('/super_point')
        if int(point) < 0:
            redirect('/super_point')
        point: int = int(point)
        msg: str = form.data['contents']
        hashed_id: str = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret: Secret = Secret.objects.get(id_hash=hashed_id)

        sender_private_key: str = secret.private_key
        sender_blockchain_address: str = user.blockchain_address
        recipient_blockchain_address: List[str] = user_address
        sender_public_key: str = secret.public_key
        value: int = int(point)

        transaction: wallet.Transaction = wallet.Transaction(
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

        response: Response= requests.post(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions_super'),
            json=json_data_send, timeout=10)

        if response.status_code == 201:
            for usr in users:
                Message(contents=msg, sender=user.student_id,
                        recipient=usr.student_id, point=point).save()
        return redirect('/home')
    form: SuperPointForm = SuperPointForm()
    return render(request, 'super_point.html', {'form': form})


@login_required
def point(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect('/change?next=/point')

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)

    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
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
                    usr: User = User.objects.filter(blockchain_address=transacted_blockchain_address)[0]
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
                    transacted_blockchain_address: str = transaction['transacted_blockchain_address']
                except:
                    continue
                try:
                    if transacted_blockchain_address == 'Chain Gift':
                        transaction['name'] = 'Chain Gift'
                    else:
                        usr: User = User.objects.get(blockchain_address=transacted_blockchain_address)
                        transaction['name'] = usr
                except:
                    transaction['name'] = 'Miner'
                transaction['transacted_time'] = datetime.datetime.fromtimestamp(transaction['transacted_time'])
                if user.is_superuser:
                    params['receive'] = ''

        response: Response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
            {'blockchain_address': my_blockchain_address},
            timeout=5)
        if response.status_code == 200:
            total: int = response.json()['amount']
        else:
            total: str = ''
        params['total'] = total
        response: Response = requests.get(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'can_buy'),
            {'blockchain_address': my_blockchain_address},
            timeout=5)
        if response.status_code == 200:
            can_buy_total: int = response.json()['can_buy']
        else:
            can_buy_total: str = 0
        params['can_buy_total'] = can_buy_total
        if total and can_buy_total:
            only_send = total - can_buy_total
        else:
            only_send = 0
        params['only_send'] = only_send
        params['not_notified_message_count'] = not_notified_message_count
        return render(request, 'point.html', params, status=200)
    return JsonResponse({'message': 'fail', 'error': response.content}, status=400)


@login_required
def profile(request: HttpRequest, pk: Union[str, None] = None) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect(f'/change?next=profile/{pk}')

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)

    img_url: str = user.profile_img
    user: Union[User, Exception] = get_object_or_404(User, student_id=pk, delete_flag=False)
    if user.is_superuser and not request.user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        to_send: str = user.blockchain_address
        my_blockchain_address: str = request.user.blockchain_address
        if not to_send:
            return redirect(f'/profile/{pk}')
        form_data: PointForm = PointForm(request.POST)
        if not form_data.is_valid():
            return HttpResponse('error')
        message: str = form_data.data['contents']

        if not message:
            return HttpResponse('message none')
        value: str = str(form_data.data['point'])

        if not value.isdigit() or int(value) <= 0:
            return redirect(f'/super_point')

        hashed_id: str = hashlib.sha256(request.user.student_id.encode()).hexdigest()
        secret: Secret = Secret.objects.get(id_hash=hashed_id)
        sender_private_key: str = secret.private_key
        sender_blockchain_address: str = my_blockchain_address
        recipient_blockchain_address: str = to_send
        sender_public_key: str = secret.public_key
        value: int = int(value)

        transaction: wallet.Transaction = wallet.Transaction(
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

        response: Response = requests.post(
            urllib.parse.urljoin('http://127.0.0.1:5000', 'transactions'),
            json=json_data_return, timeout=10)
        if response.status_code == 201:
            if message:
                Message(contents=message, sender=request.user.student_id,
                        recipient=user.student_id, point=value).save()
                MessageCount(from_grade_id=user.grade_id, from_class_id=user.class_id,
                             to_grade_id=user.grade_id, to_class_id=user.class_id).save()
            return redirect(f'/profile/{pk}')
        else:
            return redirect('/home/')
    params = {
        'username': user.username,
        'grade_id': user.grade_id,
        'class_id': user.class_id,
        'img_url': user.profile_img,
        'not_notified_message_count': not_notified_message_count
    }

    my_blockchain_address: str = request.user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    params['total'] = total
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'can_buy'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        can_buy_total: int = response.json()['can_buy']
    else:
        can_buy_total: str = ''
    if total and can_buy_total:
        only_send = total - can_buy_total
    else:
        only_send = ''
    params['only_send'] = only_send
    if user.birthday:
        birthday: datetime.date = user.birthday
        params['birthday'] = birthday
    if user.profile_message:
        user_profile = user.profile_message
        params['profile'] = user_profile

    if request.method == 'GET':
        user: User = request.user
        if user.is_authenticated:
            if user.student_id == pk:
                params['self_user'] = True
            else:
                params['self_user'] = False
        else:
            params['self_user'] = False
    params['user_img'] = img_url
    form: PointForm = PointForm(initial={'point': user.template_point})
    params['form'] = form
    return render(request, 'profile.html', params)


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect(f'/change?next=login_flag')
    if request.method == 'POST':
        before: str = user.profile_img
        form: UserUpdateForm = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()

            user: Union[User, Exception] = get_object_or_404(User, student_id=user.student_id)
            after: str = user.profile_img
            if after and before != after:
                img = Image.open(f'media/{after}')
                img_resize = img.resize((256, 256))
                img_resize.save(f'media/{after}')
            if before and not after:
                os.remove(f'media/{before}')
            if (before and after) and (before != after):
                os.remove(f'media/{before}')
            return redirect(f'/profile/{user.pk}')
        params = {'form': form, 'message': '値が不正です'}
        return render(request, 'edit_profile.html', params)

    form: UserUpdateForm = UserUpdateForm(initial={'profile_img': user.profile_img,
                                   'birthday': user.birthday,
                                   'profile_message': user.profile_message})
    return render(request, 'edit_profile.html', {'form': form})


def shop_home(request):
    data = Goods.objects.all()
    return render(request, 'shop.html', {'data': data})


@login_required
def signup(request: HttpRequest) -> HttpResponse:
    user: HttpResponse = request.user
    if not user.is_superuser:
        return redirect('/home')
    if request.method == 'POST':
        form: SignUpForm = SignUpForm(request.POST)
        data: form.data = form.data
        password_by_list: List[str] = [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
        password: str = ''.join(password_by_list)

        b58str: base58.b58decode = base58.b58encode(password.encode()).decode('utf-8')
        password: str = b58str[:8]
        try:
            User.objects.get(student_id=data['student_id'])
            return redirect('/management')
        except:
            user: User = User(
                username=data['username'],
                email=data['email'],
                class_id=data['class_id'])
        user.set_password(password)
        user.furigana = data['furigana']
        user.student_id = data['student_id']
        user.grade_id = 1
        w = wallet.Wallet()
        user.blockchain_address: str = w.blockchain_address
        qr_img_name = make_qr(user.student_id)
        user.qr_img = qr_img_name
        user.save()
        msg = 'ユーザーの作成に成功しました'
        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        Secret(id_hash=hashed_id, public_key=w.public_key, private_key=w.private_key).save()
        form = SignUpForm()
        hashed_id: str = hashlib.sha256(request.user.student_id.encode()).hexdigest()
        secret: Secret = Secret.objects.get(id_hash=hashed_id)
        post_transaction(sender_blockchain_address=request.user.blockchain_address,
                         sender_private_key=secret.private_key,
                         sender_public_key=secret.public_key,
                         recipient_blockchain_address=w.blockchain_address,
                         value=300)
        send_gmail(password, data['email'])
        return render(request, 'signup.html', {'form': form, 'msg': msg})

    form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@login_required
def create_test(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')
    if request.method == 'POST':
        form = CreateTestForm(request.POST)
        data = form.data
        semester_choice = ((0, '学期'),
                           (1, '前'),
                           (2, '中'),
                           (3, '後'),
                           (4, '1'),
                           (5, '2'),
                           (6, '3'))
        type_choice = ((0, '種別'),
                       (1, '中間'),
                       (2, '期末'),
                       (3, 'その他'))
        year = data['year']
        semester = semester_choice[int(data['semester'])][1]
        test_type = type_choice[int(data['type'])][0]
        grade_id = data['grade_id']
        if not year.isdigit() or semester == '学期' or test_type == 0 or grade_id == '0':
            return render(request, 'create_test.html', {'form': form})
        grade_id_list = User.objects.all().values_list('grade_id', flat=True).order_by('grade_id').distinct()
        if grade_id_list:
            grade_choice = [(k + 1, str(v)) for k, v in enumerate(grade_id_list)]
        grade_id = grade_choice[int(grade_id)-1][1]
        test = Test(year=year, semester=semester, type=test_type, grade_id=grade_id)
        test.save()
        return redirect('/grades/top')

    form = CreateTestForm()
    return render(request, 'create_test.html', {'form': form})


@login_required
def goods_register(request: HttpRequest) -> HttpResponse:
    user: User = request.user
    if not user.is_superuser:
        return redirect('/home')
    if request.method == 'POST':
        form: GoodsRegisterForm = GoodsRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/goods/register')
        else:
            form: GoodsRegisterForm = GoodsRegisterForm()
            params = {'form': form, 'message': '値が不正です'}
        return render(request, 'goods_register.html', params)

    form: GoodsRegisterForm = GoodsRegisterForm()
    return render(request, 'goods_register.html', {'form': form})


def goods_db(request):
    grade_id_list = User.objects.all().values_list('grade_id', flat=True).order_by('grade_id').distinct()
    img = Image.open(f'media/smile.png')
    img_resize = img.resize((256, 256))
    img_resize.save(f'media/smile.png')
    img = Image.open(f'media/smile_dark.png')
    img_resize = img.resize((256, 256))
    img_resize.save(f'media/smile_dark.png')
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
                                    'goods_img': str(value.goods_img),
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


@login_required
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

    if request.user.delete_flag:
        return redirect('/logout')

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=request.user.student_id)
    not_notified_message_count: int = len(not_notified_messages)

    my_blockchain_address: str = request.user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    if request.user.is_superuser:
        not_notified_message_count = 0

    now = datetime.datetime.now()
    month_first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_time_stamp = month_first.timestamp()

    response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'ranking'),
        {'duration': first_time_stamp},
        timeout=10)
    if response.status_code == 200:
        tmp_rank = response.json()[0]['ranking']
        # receive_ranking, send_ranking = dict(), dict()
        receive_rank = []
        send_rank = []
        for k, v in tmp_rank['receive_ranking'].items():
            user = User.objects.get(blockchain_address=k)
            receive_rank.append({'username': user.username,
                                 'point': v,
                                 'stu_id': user.student_id,
                                 'img_url': str(user.profile_img)})

        for k, v in tmp_rank['send_ranking'].items():
            user = User.objects.get(blockchain_address=k)
            send_rank.append({'username': user.username,
                              'point': v,
                              'stu_id': user.student_id,
                              'img_url': str(user.profile_img)})
        sorted_send_ranking = sorted(send_rank, key=lambda x: x['point'], reverse=True)
        sorted_receive_ranking = sorted(receive_rank, key=lambda x: x['point'], reverse=True)
        rank_idx = 1
        continuous = 0
        total_member = 0
        before_point = 0
        for user_info in sorted_send_ranking:
            total_member += 1
            if user_info['point'] == before_point:
                user_info['rank'] = rank_idx
                continuous += 1
            else:
                rank_idx = total_member
                continuous = 0
                user_info['rank'] = rank_idx
            before_point = user_info['point']
            if continuous == 0 and total_member > 10:
                break
        else:
            sorted_send_ranking = sorted_send_ranking[:total_member]

        rank_idx = 1
        continuous = 0
        total_member = 0
        before_point = 0
        for user_info in sorted_receive_ranking:
            total_member += 1
            if user_info['point'] == before_point:
                user_info['rank'] = rank_idx
                continuous += 1
            else:
                rank_idx = total_member
                continuous = 0
                user_info['rank'] = rank_idx
            if continuous == 0 and total_member > 10:
                break
        else:
            sorted_receive_ranking = sorted_receive_ranking[:total_member]

        params = {'send_ranking': sorted_send_ranking,
                  'receive_ranking': sorted_receive_ranking,
                  'not_notified_message_count': not_notified_message_count,
                  'total': total}
        return render(request, 'ranking.html', params)


@login_required
def grades(request):
    user = request.user
    if user.delete_flag:
        return redirect('/login')
    if not user.login_flag:
        return redirect('/change?next=/grades')
    all_test = list(set(Grades.objects.filter(student_id=user.student_id).values_list('test_id').order_by('-id')))
    all_test = sorted(all_test, key=lambda x: x[0], reverse=True)
    tests = []
    for test_id in all_test:
        tmp_dict = dict()
        test = Test.objects.get(id=test_id[0])
        semester = test.semester
        if test.semester not in ['前', '中', '後']:
            semester = test.semester + '学'
        if test.type == 1:
            test_type = '中間テスト'
        elif test.type == 2:
            test_type = '期末テスト'
        else:
            test_type = ''
        test_title = f'{test.year}年度 {semester}期 {test.grade_id}学年 {test_type}'
        tmp_dict['id'] = test.id
        tmp_dict['title'] = test_title
        tests.append(tmp_dict.copy())

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)
    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    if user.is_superuser:
        not_notified_message_count = 0
    params = {'total': total,
              'not_notified_message_count': not_notified_message_count,
              'tests': tests}
    return render(request, 'grades.html', params)


@login_required
def grades_detail(request, pk: int):
    user = request.user
    if user.delete_flag:
        return redirect('/login')
    if not user.login_flag:
        return redirect('/change?next=/grades')
    test = Test.objects.get(id=pk)
    grades = Grades.objects.filter(test_id=pk, student_id=user.student_id)
    test_result_info = {}
    my_total = 0
    for g in grades:
        scores_tmp_list = []
        all_members_grades_list = Grades.objects.filter(test_id=pk, subject=g.subject).values_list('score')
        try:
            my_score = Grades.objects.get(test_id=pk, subject=g.subject, student_id=user.student_id).score
            if my_score:
                my_total += my_score
        except:
            continue
        for score in all_members_grades_list:
            if score[0]:
                scores_tmp_list.append(score[0])

        if scores_tmp_list and my_score:
            scores_tmp_list.sort()
            my_rank = len(scores_tmp_list) - bisect(scores_tmp_list, my_score) + 1
            np_array = np.array(scores_tmp_list)
            mean = np.mean(np_array)
            std = np.std(np_array)
            my_deviation = round((my_score - mean)/std * 10 + 50, 2)
            test_result_info[g.subject] = {'rank': my_rank,
                                           'score': my_score,
                                           'deviation': my_deviation}

    list_of_total = []
    for usr in User.objects.filter(grade_id=test.grade_id):
        grades = Grades.objects.filter(student_id=usr.student_id, test_id=pk)
        t = 0
        for g in grades:
            if g.score:
                t += g.score
        list_of_total.append(t)
    if list_of_total and my_total:
        list_of_total.sort()
        my_total_rank = len(list_of_total) - bisect(list_of_total, my_total) + 1
    else:
        my_total_rank = ''
    if my_total:
        test_result_info['total'] = {'score': my_total}
    if my_total and test.std_div:
        my_total_deviation = round((my_total - test.mean) / test.std_div * 10 + 50, 2)
        test_result_info['total'] = {'rank': my_total_rank,
                                     'score': my_total,
                                     'deviation': my_total_deviation}
    semester = test.semester
    if test.semester not in ['前', '中', '後']:
        semester = test.semester + '学'
    if test.type == 1:
        test_type = '中間テスト'
    elif test.type == 2:
        test_type = '期末テスト'
    else:
        test_type = ''
    test_title = f'{test.year}年度 {semester}期 {test.grade_id}学年 {test_type}'
    subjects_query = TestSubject.objects.filter(test_id=pk).values_list('subject')
    subjects_list = []
    for subject in subjects_query:
        subjects_list.append(subject[0])
    params = {'title': test_title, 'result': test_result_info, 'subjects': subjects_list}

    not_notified_messages: QuerySet = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count: int = len(not_notified_messages)
    my_blockchain_address: str = user.blockchain_address
    response: Response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total: int = response.json()['amount']
    else:
        total: str = ''
    if user.is_superuser:
        not_notified_message_count = 0
    params['total'] = total
    params['not_notified_message_count'] = not_notified_message_count
    return render(request, 'grades_detail.html', params)


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
    return redirect('/change')


@login_required
def settings(request):
    user = request.user
    if user.delete_flag:
        return redirect('/logout')
    if not user.login_flag:
        return redirect('/change?next=/grades')
    not_notified_messages = Message.objects.filter(notify_flag=0, recipient=user.student_id)
    not_notified_message_count = len(not_notified_messages)

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
    response = requests.get(
        urllib.parse.urljoin('http://127.0.0.1:5000', 'amount'),
        {'blockchain_address': user.blockchain_address},
        timeout=5)
    if response.status_code == 200:
        total = response.json()['amount']
    else:
        total = ''
    params = {'form': form, 'not_notified_message_count': not_notified_message_count,
              'total': total}
    return render(request, 'settings.html', params)


@login_required
def grades_edit(request, pk: int):
    if not request.user.is_superuser:
        return redirect('home')
    form = AddSubjectForm()
    subjects = TestSubject.objects.filter(test_id=pk)
    t = Test.objects.get(id=pk)
    semester = t.semester
    if t.semester not in ['前', '中', '後']:
        semester = t.semester + '学'
    if t.type == 1:
        test_type = '中間テスト'
    elif t.type == 2:
        test_type = '期末テスト'
    else:
        test_type = ''
    test_title = f'{t.year}年度 {semester}期 {t.grade_id}学年 {test_type}'
    if request.method == 'POST':
        for v in request.POST:
            if v == "csrfmiddlewaretoken":
                continue
            id_and_sub = v.split('___')
            try:
                Grades.objects.filter(student_id=id_and_sub[0],
                                      subject=subjects[int(id_and_sub[1])].subject, test_id=pk)[0]
                if request.POST.get(v):
                    Grades.objects.filter(student_id=id_and_sub[0],
                                          subject=subjects[int(id_and_sub[1])].subject, test_id=pk).update(score=int(request.POST.get(v)))
                else:
                    Grades.objects.filter(student_id=id_and_sub[0],
                                          subject=subjects[int(id_and_sub[1])].subject, test_id=pk).update(score=None)
            except:
                Grades(student_id=id_and_sub[0], subject=subjects[int(id_and_sub[1])].subject, test_id=pk).save()
                if request.POST.get(v):
                    Grades.objects.filter(student_id=id_and_sub[0],
                                          subject=subjects[int(id_and_sub[1])].subject, test_id=pk).update(score=int(request.POST.get(v)))

    users = User.objects.filter(grade_id=t.grade_id).values('student_id').distinct()
    name_and_grades = dict()
    try:
        user_total_scores_list = []
        for user in users:
            usr = User.objects.get(student_id=user['student_id'])
            name_and_grades[usr.username] = dict()
            name_and_grades[usr.username]['furigana'] = usr.furigana
            name_and_grades[usr.username]['class_id'] = usr.class_id
            name_and_grades[usr.username]['student_id'] = user['student_id']
            grades_ = Grades.objects.filter(test_id=pk, student_id=user['student_id'])
            total = 0
            for g in grades_:
                if g.score:
                    total += g.score
                name_and_grades[usr.username][g.subject] = g.score
            user_total_scores_list.append(total)
        if user_total_scores_list:
            mean = sum(user_total_scores_list) / len(user_total_scores_list)
            t.mean = mean
            t.save()
        sorted_user_list = sorted(name_and_grades.items(), key=lambda x: ((natural_keys(x[1]['class_id'])),
                                                                          x[1]['furigana']))

    except:
        sorted_user_list = {}
    if sorted_user_list:
        sorted_user_list_by_class = []
        sorted_user_list_by_class_tmp = []
        tmp_class_id = sorted_user_list[0][1]['class_id']
        for sorted_user in sorted_user_list:
            if tmp_class_id != sorted_user[1]['class_id']:
                tmp_class_id = sorted_user[1]['class_id']
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp.copy())
                sorted_user_list_by_class_tmp = [sorted_user]
                continue
            sorted_user_list_by_class_tmp.append(sorted_user)
        else:
            if sorted_user_list_by_class_tmp:
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp)
        sorted_user_list = sorted_user_list_by_class
    if request.method == 'POST':
        for subject in subjects:
            scores = Grades.objects.filter(subject=subject.subject, test_id=pk)
            np_list = np.array([])
            for score in scores:
                if score.score in [None, '']:
                    np_list = np.append(np_list, np.nan)
                else:
                    np_list = np.append(np_list, score.score)
            test = TestSubject.objects.get(test_id=pk, subject=subject.subject)
            test.std_div = np.nanstd(np_list)
            try:
                test.save()
            except ValueError:
                pass
        all_scores = Grades.objects.filter(test_id=pk).values_list('score', flat=True).exclude(score=None)
        try:
            np_array = np.array(all_scores)
            std_div = np.nanstd(np_array)
            t = Test.objects.get(id=pk)
            t.std_div = std_div
            t.save()
        except:
            pass
    if request.method == 'POST':
        return redirect(f'/grades/result/{pk}/normal')
    return render(request, 'grades_edit.html', {'form': form, 'self_pk': pk, 'subjects': subjects,
                                                'user_list': sorted_user_list, 'test_title': test_title})


@login_required
def add_subject(request, pk: int):
    if not request.user.is_superuser:
        return redirect('/home')
    form = AddSubjectForm(request.POST)
    subject = form.data['subject']
    if subject == '':
        return redirect(f'/grades/edit/{pk}')
    try:
        TestSubject.objects.get(test_id=pk, subject=subject)
    except:
        TestSubject(test_id=pk, subject=subject).save()
        grade = Test.objects.get(id=pk).grade_id
        users = User.objects.filter(grade_id=grade)
        for user in users:
            Grades(test_id=pk, subject=subject, student_id=user.student_id).save()
    return redirect(f'/grades/edit/{pk}')


@login_required
def delete_subject(request, pk: int):
    if not request.user.is_superuser:
        return redirect('/home')
    form = AddSubjectForm(request.POST)
    subject = form.data['subject']
    try:
        TestSubject.objects.filter(test_id=pk, subject=subject)[0]
    except:
        return redirect(f'/grades/edit/{pk}')
    TestSubject.objects.filter(test_id=pk, subject=subject).delete()
    try:
        Grades.objects.filter(test_id=pk, subject=subject).delete()
    except:
        pass
    return redirect(f'/grades/edit/{pk}')


@login_required
def test_delete(request):
    if not request.user.is_superuser:
        return redirect('/home')
    test_id = request.GET.get('id')
    Test.objects.filter(id=test_id).delete()
    TestSubject.objects.filter(test_id=test_id).delete()
    Grades.objects.filter(test_id=test_id).delete()
    return redirect('/grades/top')


@login_required
def grades_top(request):
    if not request.user.is_superuser:
        return redirect('/home')
    test_list = Test.objects.all().order_by('-year', '-semester', '-id')
    if request.method == 'POST':
        form = TestSearchForm(request.POST)
        year = form.data['year']
        if year:
            test_list = Test.objects.filter(year=int(year)).order_by('-year', '-semester', '-id')
            form = TestSearchForm(initial={'year': year})
    else:
        form = TestSearchForm()
    page_obj = paginate_queryset(request, test_list, 20)
    params = {
        'form': form,
        'test_list': page_obj.object_list,
        'page_obj': page_obj,
    }
    return render(request, 'grades_top.html', params)


@login_required
def test_result_super(request, pk: int, order: str):
    if not request.user.is_superuser:
        return redirect('/home')
    form = AddSubjectForm()
    subjects = TestSubject.objects.filter(test_id=pk)
    t = Test.objects.get(id=pk)
    semester = t.semester
    if t.semester not in ['前', '中', '後']:
        semester = t.semester + '学'
    if t.type == 1:
        test_type = '中間テスト'
    elif t.type == 2:
        test_type = '期末テスト'
    else:
        test_type = ''
    test_title = f'{t.year}年度 {semester}期 {t.grade_id}学年 {test_type}'
    users = User.objects.filter(grade_id=t.grade_id).values('student_id').distinct()
    name_and_grades = dict()
    sorted_user_list = {}
    try:
        array_for_average = list()
        for user in users:
            usr = User.objects.get(student_id=user['student_id'])
            name_and_grades[usr.username] = dict()
            name_and_grades[usr.username]['furigana'] = usr.furigana
            name_and_grades[usr.username]['class_id'] = usr.class_id
            name_and_grades[usr.username]['student_id'] = user['student_id']
            grades = Grades.objects.filter(test_id=pk, student_id=user['student_id'])
            total = 0
            subject_count = 0
            for g in grades:
                name_and_grades[usr.username][g.subject] = g.score
                if type(g.score) is int or type(g.score) is float:
                    total += g.score
                    subject_count += 1
            name_and_grades[usr.username]['total'] = total
            array_for_average.append(total)
            if subject_count >= 1:
                name_and_grades[usr.username]['average'] = round(total / subject_count, 1)
            else:
                name_and_grades[usr.username]['average'] = 0

        total_average = round(t.mean, 2)
        std_div_of_total = round(t.std_div, 2)
        if order == 'normal':
            sorted_user_list = sorted(name_and_grades.items(), key=lambda x: ((natural_keys(x[1]['class_id'])),
                                                                              x[1]['furigana']))
        elif order == 'ranking':
            sorted_user_list = sorted(name_and_grades.items(), key=lambda x: x[1]['total'], reverse=True)
            return render(request, 'test_result.html', {'form': form, 'self_pk': pk, 'subjects': subjects,
                                                        'user_list': sorted_user_list, 'test_title': test_title,
                                                        'total_average': total_average,
                                                        'std_div_of_total': std_div_of_total, 'order': order})

    except:
        sorted_user_list = {}
        total_average = ''
        std_div_of_total = ''
    if sorted_user_list:
        sorted_user_list_by_class = []
        sorted_user_list_by_class_tmp = []
        tmp_class_id = sorted_user_list[0][1]['class_id']
        for sorted_user in sorted_user_list:
            if tmp_class_id != sorted_user[1]['class_id']:
                tmp_class_id = sorted_user[1]['class_id']
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp.copy())
                sorted_user_list_by_class_tmp = [sorted_user]
                continue
            sorted_user_list_by_class_tmp.append(sorted_user)
        else:
            if sorted_user_list_by_class_tmp:
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp)
        sorted_user_list = sorted_user_list_by_class
    t.mean = total_average
    t.save()
    return render(request, 'test_result.html', {'form': form, 'self_pk': pk, 'subjects': subjects,
                                                'user_list': sorted_user_list, 'test_title': test_title, 'order': order,
                                                'total_average': total_average, 'std_div_of_total': std_div_of_total})


@login_required
def return_csv(request, pk: int, order: str):
    if not request.user.is_superuser:
        return redirect('/home')
    subjects = TestSubject.objects.filter(test_id=pk)
    t = Test.objects.get(id=pk)
    users = Grades.objects.filter(test_id=pk).values('student_id').distinct()
    name_and_grades = dict()
    try:
        for user in users:
            usr = User.objects.get(student_id=user['student_id'])
            name_and_grades[usr.username] = dict()
            name_and_grades[usr.username]['furigana'] = usr.furigana
            name_and_grades[usr.username]['class_id'] = usr.class_id
            name_and_grades[usr.username]['student_id'] = user['student_id']
            for s in subjects:
                try:
                    g = Grades.objects.get(test_id=pk, student_id=user['student_id'], subject=s.subject)
                    name_and_grades[usr.username][s.subject] = g.score
                except:
                    name_and_grades[usr.username][s.subject] = None
        sorted_user_list = sorted(name_and_grades.items(), key=lambda x: (natural_keys(x[1]['class_id']),
                                                                          x[1]['furigana']))
    except:
        sorted_user_list = {}
    if sorted_user_list and order == 'normal':
        sorted_user_list_by_class = []
        sorted_user_list_by_class_tmp = []
        tmp_class_id = sorted_user_list[0][1]['class_id']
        for sorted_user in sorted_user_list:
            if tmp_class_id != sorted_user[1]['class_id']:
                tmp_class_id = sorted_user[1]['class_id']
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp.copy())
                sorted_user_list_by_class_tmp = [sorted_user]
                continue
            sorted_user_list_by_class_tmp.append(sorted_user)
        else:
            if sorted_user_list_by_class_tmp:
                sorted_user_list_by_class.append(sorted_user_list_by_class_tmp)
        sorted_user_list = sorted_user_list_by_class

    subjects_str = list(map(lambda s: s.subject, subjects))
    header = ['名前'] + subjects_str + ['合計', '平均']
    data = np.array([header])

    if order == 'normal':
        for sorted_users in sorted_user_list:
            class_row = ['' for _ in (range(len(subjects_str) + 3))]
            class_row[0] = sorted_users[0][1]['class_id'] + 'クラス'
            data = np.append(data, np.array([class_row.copy()]), axis=0)
            for sorted_user in sorted_users:
                total = 0
                subject_count = 0
                user_info = list()
                name = User.objects.get(student_id=sorted_user[1]['student_id']).username
                user_info.append(name)
                for k, v in sorted_user[1].items():
                    if k in ['furigana', 'class_id', 'student_id']:
                        continue
                    user_info.append(v)
                    if v is not np.nan and v is not None:
                        subject_count += 1
                        total += v
                else:
                    user_info.append(total)
                    if subject_count >= 1:
                        user_info.append(round(total/subject_count, 1))
                    else:
                        user_info.append(0)
                data = np.append(data, np.array([user_info.copy()]), axis=0)
    elif order == 'ranking':
        not_order_list = list()
        for sorted_user in sorted_user_list:
            total = 0
            subject_count = 0
            user_info = list()
            name = User.objects.get(student_id=sorted_user[1]['student_id']).username
            user_info.append(name)
            for k, v in sorted_user[1].items():
                if k in ['furigana', 'class_id', 'student_id']:
                    continue
                user_info.append(v)
                if v is not np.nan and v is not None:
                    subject_count += 1
                    total += v
            else:
                user_info.append(total)
                if subject_count >= 1:
                    user_info.append(round(total/subject_count, 1))
                else:
                    user_info.append(0)
            not_order_list.append(user_info.copy())
        subjects_str = list(map(lambda s: s.subject, subjects))
        header = ['名前'] + subjects_str + ['合計', '平均']
        ordered_list = sorted(not_order_list, reverse=True, key=lambda x: x[-2])
        ordered_list.insert(0, header)
        data = np.array(ordered_list)

    np.savetxt(f'media/{t.year}-{t.grade_id}_test_result.csv', data, delimiter=",", fmt='%s')
    response = HttpResponse(open(f'media/{t.year}-{t.grade_id}_test_result.csv', 'rb').read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{t.year}-{t.grade_id}_test_result.csv"'
    os.remove(f'media/{t.year}-{t.grade_id}_test_result.csv')
    return response


@login_required
def grades_super_point(request, pk: int):
    user = request.user
    if not user.is_superuser:
        return redirect('/home')

    if request.method == 'POST':
        t = Test.objects.get(id=pk)
        grade_id = t.grade_id
        users = User.objects.exclude(delete_flag=True).filter(grade_id=grade_id)
        id_and_total = list()
        for usr in users:
            total = 0
            scores = Grades.objects.filter(student_id=usr.student_id).exclude(score=None).values_list('score')
            if scores:
                for score in scores[0]:
                    total += score
            id_and_total.append((usr.student_id, total))
        sorted_id_and_total = sorted(id_and_total, reverse=True, key=lambda x: x[1])

        form = GradesPointForm(request.POST)
        point = str(form.data['point'])
        top_count = str(form.data['top_count'])
        if not point.isdigit() or not top_count.isdigit():
            return redirect('/super_point')
        if int(point) < 0 or int(top_count) < 0:
            return redirect('/super_point')
        point = int(point)
        top_count = int(top_count)
        top_count_ = 1
        for idx, user_score in enumerate(sorted_id_and_total[top_count_-1:]):
            if top_count == len(sorted_id_and_total):
                break
            if user_score[1] == sorted_id_and_total[top_count_+idx][1]:
                top_count += 1
            else:
                break

        to_send_users = list()
        for user_and_total in sorted_id_and_total[:top_count]:
            to_send_users.append(User.objects.get(student_id=user_and_total[0]))

        user_address = list(map(lambda u: u.blockchain_address, to_send_users))

        hashed_id = hashlib.sha256(user.student_id.encode()).hexdigest()
        secret = Secret.objects.get(id_hash=hashed_id)

        sender_private_key = secret.private_key
        sender_blockchain_address = 'Grades Chain Gift'
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
            semester = t.semester
            if t.semester not in ['前', '中', '後']:
                semester = t.semester + '学'
            if t.type == 1:
                test_type = '中間テスト'
            elif t.type == 2:
                test_type = '期末テスト'
            else:
                test_type = ''
            msg = f'{t.year}年度 {semester}期 {t.grade_id}学年 {test_type}'
            for usr in to_send_users:
                Message(contents=f'{msg} 成績上位ポイント', sender=user.student_id,
                        recipient=usr.student_id, point=point).save()
        return redirect('/home')
    form = GradesPointForm()
    t = Test.objects.get(id=pk)
    semester = t.semester
    if t.semester not in ['前', '中', '後']:
        semester = t.semester + '学'
    if t.type == 1:
        test_type = '中間テスト'
    elif t.type == 2:
        test_type = '期末テスト'
    else:
        test_type = ''
    msg = f'{t.year}年度 {semester}期 {t.grade_id}学年 {test_type}'
    return render(request, 'super_point.html', {'form': form, 'msg': msg})


@login_required
def super_update(request):
    if not request.user.is_superuser:
        return redirect('home')
    form = AddSubjectForm()
    user_list: QuerySet = User.objects.all()\
        .extra(select={'my_grade_id': 'CAST(class_id AS INTEGER)', 'my_class_id': 'CAST(class_id AS INTEGER)'}) \
        .order_by('my_grade_id', 'my_class_id', 'furigana')
    if request.method == 'POST':
        print(request.POST)
        all_student_id = []
        for usr in user_list:
            all_student_id.append(usr.student_id)
        for stu_id in all_student_id:
            if request.POST.get(f'{stu_id}___delete'):
                User.objects.filter(student_id=stu_id).delete()
                continue
            User.objects.filter(student_id=stu_id).update(grade_id=request.POST.get(f'{stu_id}___grade_id'),
                                                          class_id=request.POST.get(f'{stu_id}___class_id'),
                                                          delete_flag=bool(request.POST.get(f'{stu_id}___delete_flag'))
                                                          )
        return redirect(f'/super_update')
    return render(request, 'super_update.html', {'form': form, 'user_list': user_list})


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

    body = 'chain gift\nパスワード: ' + password
    if query:
        subject = 'パスワード再発行'
        contents = f'下記のリンクにアクセス後、登録されているメールアドレス宛てに新パスワードを送信します。\nhttp://127.0.0.1:8000/forget_change?rand_query={query}&email={email}'
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


@register.filter
def get_item(dictionary, key):
    if dictionary.get(key) is None:
        return ''
    return dictionary.get(key)


@register.filter
def return_score(dictionary, key):
    if dictionary.get(key) is None:
        return ''
    inner_dict = dictionary.get(key)
    if inner_dict.get('score') is None:
        return ''
    return inner_dict.get('score')


@register.filter
def return_rank(dictionary, key):
    if dictionary.get(key) is None:
        return ''
    inner_dict = dictionary.get(key)
    if inner_dict.get('rank') is None:
        return ''
    return inner_dict.get('rank')


@register.filter
def return_deviation(dictionary, key):
    if dictionary.get(key) is None:
        return ''
    inner_dict = dictionary.get(key)
    if inner_dict.get('deviation') is None:
        return ''
    return inner_dict.get('deviation')


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]
