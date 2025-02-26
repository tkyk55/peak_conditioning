from django import forms
from datetime import datetime, timedelta
from django.utils import timezone

# 時間の選択肢を生成する関数
def generate_time_choices_staff(start_hour=9, end_hour=20):
    choices = []
    base_time = datetime(2000, 1, 1, start_hour, 0)  # 開始時間を9時とする
    while base_time.hour < end_hour or (base_time.hour == end_hour and base_time.minute == 45):
        time_str = base_time.strftime('%H:%M')  # 表示形式: 09:00, 09:15, ...
        choices.append((time_str, time_str))  # (value, label)形式
        base_time += timedelta(minutes=15)  # 15分ずつ追加
    return choices

# 時間の選択肢を生成する関数
def generate_time_choices_booking(start_hour=9, end_hour=19):
    choices = []
    base_time = datetime(2000, 1, 1, start_hour, 0)  # 開始時間を9時とする
    while base_time.hour < end_hour or (base_time.hour == end_hour and base_time.minute == 00):
        time_str = base_time.strftime('%H:%M')  # 表示形式: 09:00, 09:15, ...
        choices.append((time_str, time_str))  # (value, label)形式
        base_time += timedelta(minutes=15)  # 15分ずつ追加
    return choices


class MemberSearchForm(forms.Form):
    member_no = forms.CharField(label='会員番号', required=False)
    first_name = forms.CharField(max_length=30, label='姓', required=False)
    last_name = forms.CharField(max_length=30, label='名' , required=False)
    tel_number = forms.CharField(max_length=15, label='電話', required=False)

class MemberForm(forms.Form):
    member_no = forms.CharField(label='会員番号')
    is_active = forms.BooleanField(label='退会' , required=False)
    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    sex = forms.IntegerField(label='性別')
    birthday = forms.DateField(label='生年月日', required=False)
    email = forms.EmailField(label='Mail', required=False)
    tel_number = forms.CharField(max_length=15, label='電話', required=False)
    num_contracts = forms.IntegerField(label='契約回数', required=False)
    stat_date = forms.DateField(label='契約開始日', required=False)
    end_date = forms.DateField(label='契約終了日' , required=False)
    is_shoes_custody = forms.BooleanField(label='靴預かり' , required=False)
    amount_money = forms.IntegerField(label='口座引落金額', required=False)
    memo = forms.CharField(label='メモ', required=False)

class NotificationForm(forms.Form):
    notice = forms.CharField(label='おしらせ', widget=forms.Textarea(), required=False)

class StaffInputForm(forms.Form):
    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    is_active = forms.BooleanField(label='アクティブ', required=False)
    memo = forms.CharField(label='メモ', required=False)

class StaffWorkInputForm(forms.Form):
    TIME_CHOICES = generate_time_choices_staff()
    start = forms.ChoiceField(
        label='仕事開始時間',
        required=True,
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control_staff_work'})
    )
    end = forms.ChoiceField(
        label='仕事終了時間',
        required=True,
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control_staff_work'})
    )

class StaffBookingInputForm(forms.Form):
    TIME_CHOICES = generate_time_choices_booking()
    booking_id = forms.IntegerField(label='予約ID', required=False)
    start = forms.ChoiceField(
        label='開始時間',
        required=True,
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control_staff_work'})
    )
    end = forms.DateTimeField(
        label='終了時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_booking'}),
    )
    training_no = forms.IntegerField(label='トレーニングNo', required=False)

class StaffClosingInputForm(forms.Form):
    TIME_CHOICES = generate_time_choices_staff()
    closing_id = forms.IntegerField(label='予約ID', required=False)
    start = forms.ChoiceField(
        label='ブロック開始時間',
        required=True,
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control_staff_work'})
    )
    end = forms.ChoiceField(
        label='ブロック終了時間',
        required=False,
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control_staff_work'})
    )
    training_id = forms.IntegerField(label='トレーニングID', required=False)
    training_no = forms.IntegerField(label='トレーニングNo', required=False)

class StaffExBookingForm(forms.Form):
    GENDER_CHOICES = [
        ('0', '選択しない'),
        ('1', '男性'),
        ('2', '女性'),
    ]

    AGE_CHOICES = [
        ('10', '0~10代'),
        ('20', '20代'),
        ('30', '30代'),
        ('40', '40代'),
        ('50', '50代'),
        ('60', '60代'),
        ('70', '70代'),
        ('80', '80代以上'),
    ]

    PEOPLE_CHOICES = [
        ('0', '1名'),
        ('1', '2名'),
        ('2', '3名以上'),
    ]

    OBJECTS_CHOICES = [
        (0, '痛みや不調の改善'),
        (1, '姿勢改善'),
        (2, '健康増進'),
        (3, '筋力アップ'),
        (4, 'シニアの運動'),
        (5, '運動不足解消'),
        (6, 'スポーツのレベルアップ'),
        (7, '怪我の再発予防'),
        (8, 'シェイプアップ'),
        (9, 'その他')
    ]

    first_name = forms.CharField(label='姓', max_length=30)
    last_name = forms.CharField(label='名', max_length=30)
    start = forms.DateTimeField(label='開始時間', required=False)
    end = forms.DateTimeField(label='終了時間', required=False)
    sex = forms.ChoiceField(label='性別', choices=GENDER_CHOICES, required=False)
    age = forms.ChoiceField(label='年齢', choices=AGE_CHOICES, required=False)
    people = forms.ChoiceField(label='人数', choices=PEOPLE_CHOICES, required=False)
    email = forms.EmailField(label='Mail')
    tel_number = forms.CharField(label='携帯電話番号', max_length=15, required=False)
    objective = forms.MultipleChoiceField(label='目的', choices=OBJECTS_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)
    remarks = forms.CharField(label='備考', widget=forms.Textarea(), required=False)
    ex_booking_id = forms.IntegerField(label='体験予約ID', required=False)
