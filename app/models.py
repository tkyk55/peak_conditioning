from django.db import models
from accounts.models import CustomUser, Training
from django.utils import timezone
from django.core.validators import RegexValidator

class Staff(models.Model):
    user = models.OneToOneField(CustomUser, verbose_name='スタッフ', on_delete=models.CASCADE)
    role = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)

class Booking(models.Model):
    training = models.ForeignKey(Training, verbose_name='トレーニング', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    remarks = models.TextField('備考', default="", blank=True)

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        return f'{self.user} {start} ~ {end} {self.training}'

class ExBooking(models.Model):
    training = models.ForeignKey(Training, verbose_name='トレーニング', on_delete=models.CASCADE)
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    first_name = models.CharField(('姓'), max_length=30)
    last_name = models.CharField(('名'), max_length=30)
    sex = models.IntegerField(default=0)
    age = models.CharField(default=0, max_length=3)
    people = models.IntegerField(default=0)
    email = models.EmailField('メールアドレス')
    email_ch = models.EmailField('メールアドレス確認', blank=True)
    tel_number_regex = RegexValidator(regex=r'^0\d{1,4}-\d{1,4}-\d{3,4}$/', message = ("右の形式で入力してください「090-1234-5678」"))
    tel_number = models.CharField(validators=[tel_number_regex], max_length=15, verbose_name='携帯電話番号')
    objective = models.CharField(('目的'), max_length=30)
    remarks = models.TextField('伝えたいこと', default="", blank=True)

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        #email = self.normalize_email(self.email)
        #email_ch = self.normalize_email(self.email_ch)
        return f'{self.training}　{start} ~ {end} {self.first_name}　{self.last_name} {self.sex} {self.age} ' \
               f'{self.people} ' \
               f'{self.email}　{self.email_ch} {self.tel_number}' \
               f' {self.objective} {self.remarks} '

class Master(models.Model):
    category = models.CharField('カテゴリ', max_length=30)
    set_value = models.CharField('設定値', max_length=30)

    def __str__(self):
        return f'{self.category} {self.set_value}'

class Notification(models.Model):
    notice = models.TextField('おしらせ', default="", blank=True)

    def __str__(self):
        return f'{self.notice}'
