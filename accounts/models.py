from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator


class UserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    member_no = models.CharField(('会員番号'), max_length=5, null=True, blank=True)
    email = models.EmailField('メールアドレス', unique=True)
    email_verified = models.BooleanField(default=False)
    first_name = models.CharField(('姓'), max_length=30)
    last_name = models.CharField(('名'), max_length=30)
    sex = models.IntegerField('性別', default=2)
    birthday = models.DateField(('生年月日'), null=True, blank=True)
    tel_number_regex = RegexValidator(regex=r'[(]?\d{2,4}[-)]?\d{2,4}-\d{3,4}', message = ("右の形式で入力してください「090-1234-5678」"))
    tel_number = models.CharField(validators=[tel_number_regex], max_length=15, verbose_name='携帯電話番号', default="")
    num_contracts = models.IntegerField('契約回数', default=8)
    num_times = models.IntegerField('予約残回数', default=8)
    stat_date = models.DateField(('契約開始日'), null=True, blank=True)
    end_date = models.DateField(('契約終了日'), null=True, blank=True)
    is_shoes_custody = models.BooleanField(
        ('靴預り'),
        default=False,
        help_text=('靴預りありの場合はチェックを入れてください'),
    )
    amount_money = models.IntegerField('口座引落金額', default=0)
    memo = models.TextField('メモ', null=True, blank=True)

    created = models.DateField(('入会日'), null=True, blank=True)
    image = models.ImageField(upload_to='images', verbose_name='プロフィール画像', null=True, blank=True)
    is_staff = models.BooleanField(
        ('staff status'),
        default=False,
        help_text=('スタッフの場合はチェックを入れてください'),
    )
    is_active = models.BooleanField(
        ('active'),
        default=True,
        help_text=(
            'このユーザーを停止させたい場合はチェックを外してください'
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = ('user')
        verbose_name_plural = ('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

class Training(models.Model):
    name = models.CharField('トレーニング名', max_length=100)
    description = models.TextField('説明', default="", blank=True)
    experience_flg = models.IntegerField('体験フラグ', default=0)
    display_num = models.IntegerField('表示順', default=0)
    image = models.ImageField(upload_to='images', verbose_name='イメージ画像', null=True, blank=True)
    duplicates_num = models.IntegerField('重複数', default=1)
    del_flg = models.IntegerField('削除フラグ', default=0)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return self.name
