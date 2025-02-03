import calendar, json, pytz

from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from app.app_member.models import EmailTemplate, Master
from app.app_staff.models import Staff, Notification, StaffWork, ClosingDay
from datetime import datetime, date, timedelta, time

def send_custom_email(template_id, context, recipient_list, from_email):
    try:
        template = EmailTemplate.objects.get(id=template_id)
        subject = template.subject.format(**context)
        message = template.body.format(**context)

        send_mail(
            subject,
            message,
            from_email,  # settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

# メール送信入口
def send_email__function(email, context, email_templates_id):
    master_data = Master.objects.get(id=1)
    from_email = master_data.from_email
    recipient_list = [email]

    send_custom_email(email_templates_id, context, recipient_list, from_email)
    return

# 休館日検索
def find_closing_exist_days__function(closing_type, start, end, training_id, training_no):
    closing_exist_data = None
    if closing_type == 'B': # 時間帯制限
        closing_exist_data = ClosingDay.objects.filter(start__lt=end, end__gt=start, training=training_id,
                                                       closing_type__in=('B', 'G'))
    elif closing_type == 'G': # 一部時間帯制限
        closing_exist_data = ClosingDay.objects.filter(
            (Q(closing_type='G') & Q(training_no=training_no)) | Q(closing_type='B'), start__lt=end, end__gt=start,
            training=training_id)
    elif closing_type == 'C': # Close:全休
        closing_exist_data = ClosingDay.objects.filter(start__lte=end, end__gte=start, closing_type=('C'))

    return closing_exist_data

def day_start_end_setting__function(year, month, day):
    # 休館日を取得
    japan_timezone = pytz.timezone('Asia/Tokyo')  # 日本のタイムゾーンを設定

    # start section　2024/1/1 月初作成
    first_day = 1
    start_date_str = str(year) + "-" + str(month) + "-" + str(first_day) + " " + "00:00:00"  # 2024/1/1 00:00:00
    start_date_datetime = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    start_date_j = japan_timezone.localize(start_date_datetime)
    start_date = date(year, month, first_day)

    # end section
    last_day = calendar.monthrange(year=year, month=month)[1]  # 31日
    emd_date_str = str(year) + "-" + str(month) + "-" + str(last_day) + " " + "23:59:59"
    end_date_datetime = datetime.strptime(emd_date_str, '%Y-%m-%d %H:%M:%S')
    end_date_j = japan_timezone.localize(end_date_datetime)
    end_date = date(year, month, last_day)

    # today section　2024/1/xx xx:xx:xx
    today_str = str(year) + "-" + str(month) + "-" + str(day) + " " + "00:00:00"  # 2024/1/1 00:00:00
    today_datetime = datetime.strptime(today_str, '%Y-%m-%d %H:%M:%S')
    today_j = japan_timezone.localize(today_datetime)

    row = {'start_date_j': start_date_j, 'end_date_j': end_date_j, 'start_date': start_date, 'end_date': end_date,
           'last_day': last_day, 'today_j': today_j}

    return row
