from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms
from .models import User, Message, Goods


class PointForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('contents', 'point')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Contents':
                field.widget.attrs['placeholder'] = 'Message'


class GoodsRegisterForm(forms.ModelForm):
    class Meta:
        model = Goods
        fields = ('name', 'price', 'category', 'goods_img')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Image':
                field.widget.attrs['class'] = None


class TestSearchForm(forms.Form):
    year = forms.IntegerField(label='年度', required=False)


class AddSubjectForm(forms.Form):
    subject = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'dark-input'


class TestClassSearchForm(forms.Form):
    year = forms.CharField(label='クラス', required=False)


class CreateTestForm(forms.Form):
    year = forms.IntegerField(label='年度')
    grade_id_list = User.objects.all().exclude(is_superuser=True).values_list('grade_id', flat=True).order_by('grade_id').distinct()
    grade_id_list = list(grade_id_list)
    SEMESTER_CHOICE = ((0, '学期'),
                       (1, '前期'),
                       (2, '中期'),
                       (3, '後期'),
                       (4, '1学期'),
                       (5, '2学期'),
                       (6, '3学期'))
    TYPE_CHOICE = ((0, '種別'),
                   (1, '中間'),
                   (2, '期末'),
                   (3, 'その他'))
    semester = forms.ChoiceField(widget=forms.Select, choices=SEMESTER_CHOICE, label='学期')
    type = forms.ChoiceField(widget=forms.Select, choices=TYPE_CHOICE, label='テスト種別')

    GRADE_CHOICE = (tuple(grade_id_list),)
    if grade_id_list:
        GRADE_CHOICE = [(k + 1, str(v)) for k, v in enumerate(grade_id_list)]
        GRADE_CHOICE.insert(0, (0, "学年"))
    grade_id = forms.ChoiceField(widget=forms.Select, choices=GRADE_CHOICE, label='学年')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class SuperPointForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('contents', 'point')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Contents':
                field.widget.attrs['placeholder'] = 'メッセージ'


class GradesPointForm(forms.Form):
    point = forms.IntegerField(label='point')
    top_count = forms.IntegerField(label='top_count')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'top_count':
                field.widget.attrs['placeholder'] = '上位人数'
            if field.label == 'point':
                field.widget.attrs['placeholder'] = 'ポイント'


class LoginForm(AuthenticationForm):
    """ログオンフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label   


class SignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('student_id', 'class_id', 'username', 'furigana', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserSearchForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('grade_id', 'class_id')


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('profile_img', 'birthday', 'profile_message')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Image':
                field.widget.attrs['class'] = None

            if field.label == '誕生日':
                field.widget.attrs['id'] = 'datepicker'
                field.widget.attrs['autocomplete'] = 'off'


class UserSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('dark_mode', 'template_point')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Dark mode':
                field.widget.attrs['class'] = 'toggle_button'
                field.widget.attrs['style'] = 'margin: 0; outline: 0 !important;'
                field.widget.attrs['onclick'] = 'change_dark()'
                field.widget.attrs['data-off-label'] = 'OFF'
                field.widget.attrs['data-on-label'] = 'ON'
            if field.label == 'Template point':
                field.label = 'ポイント設定'


class SuperUserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('grade_id', 'class_id', 'email', 'username', 'furigana', 'delete_flag')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Delete flag':
                field.label = '削除フラグ'


class ImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('profile_img',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class PasswordForgetForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field.label == 'Old password':
                field.widget.attrs['placeholder'] = "現在のパスワード"
            if field.label == 'New password':
                field.widget.attrs['placeholder'] = "新しいパスワード"
            if field.label == 'New password confirmation':
                field.widget.attrs['placeholder'] = "新しいパスワード(確認)"
