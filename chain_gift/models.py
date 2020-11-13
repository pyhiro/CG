from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractBaseUser, PermissionsMixin):
    user_vali = UnicodeUsernameValidator()
    username = models.CharField(_('名前'), max_length=150, validators=[user_vali])
    email = models.EmailField(_('メール'), unique=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    student_id = models.CharField(_('学籍番号'), max_length=10, primary_key=True)
    furigana = models.CharField(_('ふりがな'), max_length=30)
    birth_day = models.DateField(_('誕生日'), blank=True, null=True)
    blockchain_address = models.CharField(blank=False)
    class_id = models.IntegerField(_('クラス'), max_length=2)
    grade_id = models.IntegerField(_('学年'), max_length=1, blank=False, default=1)
    login_flag = models.BooleanField()
    delete_flag = models.BooleanField()
    profile_img = models.CharField(_('image'), blank=True, null=True)
    qr_img = models.CharField(_('QR'), max_length=18, blank=True, null=True)
    profile_message = models.TextField(_('プロフィール'), max_length=200, blank=True, null=True)
    login_missed = models.IntegerField(max_length=1, default=0)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    STUDENT_ID_FIELD = 'student_id'
    FURIGANA_FIELD = 'furigana'
    BIRTHDAY_FIELD = 'birth_day'
    BLOCKCHAIN_ADDRESS_FIELD = 'blockchain_address'
    CLASS_ID_FIELD = 'class_id'
    GRADE_ID_FIELD = 'grade_id'
    LOGIN_FLAG_FIELD = 'login_flag'
    DELETE_FLAG_FIELD = 'delete_flag'
    PROFILE_IMG_FIELD = 'profile_img'
    QR_IMG_FIELD = 'qr_img'
    PROFILE_MESSAGE_FIELD = 'profile_message'
    LOGIN_MISSED_FIELD = 'login_missed'
    REQUIRED_FIELDS = ['email', 'username', 'student_id', 'furigana', 'class_id']

    def __str__(self):
        return self.username


class Secret(models.Model):
    id_hash = models.CharField(primary_key=True)
    password = models.CharField(blank=False)
    public_key = models.CharField(blank=False)
    private_key = models.CharField(blank=False)


class Message(models.Model):
    contents = models.TextField(max_length=200, blank=True)
    sender = models.CharField(max_length=10, blank=False)
    recipient = models.CharField(max_length=10, blank=False)
    time_of_message = models.DateTimeField(null=True)
    read_flag = models.BooleanField()

    def __str__(self):
        return self.contents


class Goods(models.Model):
    price = models.IntegerField()
    name = models.CharField()
    person = models.IntegerField(max_length=10)

    def __str__(self):
        return self.name


