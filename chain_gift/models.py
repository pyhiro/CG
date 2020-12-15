from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractBaseUser, PermissionsMixin):
    user_vali = UnicodeUsernameValidator()

    is_staff = models.BooleanField(_('staff status'), default=False)

    student_id = models.CharField(_('学籍番号'), max_length=10, primary_key=True)
    email = models.EmailField(_('email'), unique=True, blank=False)
    blockchain_address = models.CharField(max_length=150, blank=False)
    username = models.CharField(_('名前'), max_length=150, validators=[user_vali])
    furigana = models.CharField(_('ふりがな'), max_length=30)

    birth_day = models.DateField(_('誕生日'), blank=True, null=True)

    grade_id = models.IntegerField(_('学年'), blank=True, null=False, default=1)
    class_id = models.IntegerField(_('クラス'), blank=True, null=False)

    # profile_img = models.CharField(_('image'), max_length=150, blank=True, null=True)
    profile_img = models.ImageField(_('image'), upload_to='', blank=True, null=True)
    qr_img = models.CharField(_('QR'), max_length=18, blank=True, null=True)

    profile_message = models.TextField(_('プロフィール'), max_length=200, blank=True, null=True)

    login_missed = models.IntegerField(default=0)
    login_flag = models.BooleanField(default=False)
    delete_flag = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)

    password_change_query = models.CharField(max_length=150, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    STUDENT_NAME_FIELD = 'username'
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
    REQUIRED_FIELDS = ['student_id', 'username', 'furigana', 'class_id']

    def __str__(self):
        return self.username


class Secret(models.Model):
    id_hash = models.CharField(primary_key=True, max_length=150)
    password = models.CharField(blank=False, max_length=150)
    public_key = models.CharField(blank=False, max_length=300)
    private_key = models.CharField(blank=False, max_length=300)


class Message(models.Model):
    contents = models.TextField(max_length=200, blank=True)
    sender = models.CharField(max_length=10, blank=False)
    recipient = models.CharField(max_length=10, blank=False)
    time_of_message = models.DateTimeField(default=timezone.now)
    read_flag = models.BooleanField(default=False, null=True)
    notify_flag = models.BooleanField(default=False, null=True)
    point = models.IntegerField(default=10, null=True, blank=False)
    recipient_delete_flag = models.BooleanField(default=False, null=True)
    sender_delete_flag = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.contents

class Goods(models.Model):
    price = models.IntegerField()
    name = models.CharField(max_length=50)
    goods_img = models.CharField(_('image'), max_length=150, blank=True, null=True)
    category = models.CharField(max_length=50, null=True)
    show = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Grades(models.Model):
    student_id = models.CharField(_('学籍番号'), max_length=10)
    year = models.IntegerField(blank=True, default=int(timezone.now().year))
    semester = models.IntegerField(default=1)
    type = models.IntegerField(default=1) #中間, 期末, other
    japanese = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    math = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    english = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    social = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    science = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    it = models.IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])


class MessageCount(models.Model):
    from_grade_id = models.IntegerField()
    from_class_id = models.IntegerField()
    to_grade_id = models.IntegerField()
    to_class_id = models.IntegerField()
    time_of_message = models.DateTimeField(default=timezone.now)
