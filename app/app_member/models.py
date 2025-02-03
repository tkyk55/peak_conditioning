from django.db import models,  IntegrityError
from accounts.models import CustomUser, Training
from django.utils import timezone
from django.core.validators import RegexValidator
import random, string


class Booking(models.Model):
    training = models.ForeignKey(Training, verbose_name='トレーニング', on_delete=models.CASCADE, related_name='booking')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE , related_name='booking')
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    training_no = models.IntegerField(default=0)
    remarks = models.TextField('備考', default="", blank=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    del_flg = models.IntegerField(default=0)

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        return f'{self.id} {self.user} {start} ~ {end} {self.training} {self.training_no}'

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class ExBooking(models.Model):
    training = models.ForeignKey(Training, verbose_name='トレーニング', on_delete=models.CASCADE, null=True)
    start = models.DateTimeField('開始時間',  null=True)
    end = models.DateTimeField('終了時間', null=True)
    first_name = models.CharField(('姓'), max_length=30, null=True)
    last_name = models.CharField(('名'), max_length=30, null=True)
    sex = models.IntegerField(default=0, null=True)
    age = models.IntegerField(default=0, null=True)
    people = models.IntegerField(default=0, null=True)
    email = models.EmailField('メールアドレス')
    tel_number = models.CharField(max_length=15, verbose_name='携帯電話番号', null=True)
    objective = models.CharField(('目的'), max_length=30, null=True)
    remarks = models.TextField('伝えたいこと', default="", null=True)
    url_param = models.CharField(('url_param'), default=generate_random_string, max_length=10, null=True, unique=True)
    status = models.CharField(('ステータス'), default=0, max_length=1)
    expiration_date = models.DateTimeField('有効期限', default=timezone.now, null=True)
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    updated_by = models.CharField('更新アプリ', max_length=30, null=True)
    version = models.IntegerField(default=0)
    is_valid =models.BooleanField(
        ('有効'),
        default=True,
        help_text=('有効フラグ'),
    )

    def save(self, *args, **kwargs):
        if not self.url_param:
            self.url_param = generate_random_string()

        # リトライロジック
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                super(ExBooking, self).save(*args, **kwargs)
                break  # 保存成功時にループを抜ける
            except IntegrityError as e:
                if 'unique constraint' in str(e):
                    retry_count += 1
                    self.url_param = generate_random_string()
                else:
                    raise e
        else:
            raise IntegrityError("Failed to generate a unique url_param after multiple attempts")

    def __str__(self):
        start = timezone.localtime(self.start).strftime('%Y/%m/%d %H:%M')
        end = timezone.localtime(self.end).strftime('%Y/%m/%d %H:%M')
        #email = self.normalize_email(self.email)
        #email_ch = self.normalize_email(self.email_ch)
        return f'{self.training}　{start} ~ {end} {self.first_name}　{self.last_name} {self.sex} {self.age} ' \
               f'{self.people} ' \
               f'{self.email}　{self.tel_number}' \
               f' {self.objective} {self.remarks} '

class Master(models.Model):
    #category = models.CharField('カテゴリ', max_length=30)
    #set_value = models.CharField('設定値', max_length=30)
    from_email = models.EmailField('送信元メールアドレス', default='default@example.com')
    site_url = models.URLField(max_length=200, verbose_name='サイトURL', blank=True, null=True)  # URLフィールドを追加
    shop_tel1 = models.CharField(max_length=15, verbose_name='お店電話番号1', null=True)

    def __str__(self):
        return f'{self.from_email} {self.site_url}'

class EmailTemplate(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField('作成時間', default=timezone.now)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
            return self.subject

