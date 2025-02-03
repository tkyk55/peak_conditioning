from django.db import models
from django.utils import timezone
from accounts.models import CustomUser, Training
from django.core.validators import RegexValidator

class Staff(models.Model):
    first_name = models.CharField(('姓'), max_length=31)
    last_name = models.CharField(('名'), max_length=31)
    is_active = models.BooleanField(
        ('active'),
        default=True,
        help_text=(
            'このユーザーを停止させたい場合はチェックを外してください'
        ),
    )
    memo = models.TextField('メモ', null=True, blank=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Notification(models.Model):
    notice = models.TextField('おしらせ', null=True, blank=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return f'{self.notice}'

class StaffWork(models.Model):
    staff_id = models.ForeignKey(Staff, verbose_name='スタッフ仕事', on_delete=models.CASCADE)
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    remarks = models.TextField('備考', default="", blank=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        return f'{self.staff_id} {start} ~ {end}'

class ClosingDay(models.Model):
    closing_type = models.CharField(('休日タイプ'), max_length=1, default=None)
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    training = models.ForeignKey(Training, verbose_name='トレーニング', on_delete=models.CASCADE, null=True)
    training_no = models.IntegerField(default=None, null=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        return f'{self.id} {self.closing_type} {start} ~ {end} {self.training} {self.training_no}'
