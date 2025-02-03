from django import forms
from django.utils import timezone

class BookingForm(forms.Form):
    remarks = forms.CharField(label='備考', widget=forms.Textarea(), required=False)

class ExBookingForm(forms.Form):
    GENDER_CHOICES = [
        ('0', '選択しない'),
        ('1', '男性'),
        ('2', '女性'),
    ]

    AGE_CHOICES = [
        ('10', '10代'),
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
        ('0', '痛みや不調の改善'),
        ('1', '姿勢改善'),
        ('2', '健康増進'),
        ('3', '筋力アップ'),
        ('4', 'シニアの運動'),
        ('5', '運動不足解消'),
        ('6', 'スポーツのレベルアップ'),
        ('7', '怪我の再発予防'),
        ('8', 'シェイプアップ'),
        ('9', 'その他')
    ]

    first_name = forms.CharField(label='姓', max_length=30)
    last_name = forms.CharField(label='名', max_length=30)
    start = forms.DateTimeField(label='開始時間', required=False)
    end = forms.DateTimeField(label='終了時間', required=False)
    sex = forms.ChoiceField(label='性別', choices=GENDER_CHOICES, required=True)
    age = forms.ChoiceField(label='年齢', choices=AGE_CHOICES, required=True)
    people = forms.ChoiceField(label='人数', choices=PEOPLE_CHOICES, required=True)
    email = forms.EmailField(label='Mail')
    email_ch = forms.EmailField(label='Mail確認')
    tel_number = forms.CharField(label='携帯電話番号', max_length=15, required=False)
    objective = forms.MultipleChoiceField(label='目的', choices=OBJECTS_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)
    remarks = forms.CharField(label='備考', widget=forms.Textarea(), required=False)

class ExEmailForm(forms.Form):
    email = forms.EmailField(label='Mail')