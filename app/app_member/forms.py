from django import forms
from django.utils import timezone

class BookingForm(forms.Form):
    remarks = forms.CharField(label='備考', widget=forms.Textarea(), required=False)

class ExBookingForm(forms.Form):
    first_name = forms.CharField(label='姓', max_length=30)
    last_name = forms.CharField(label='名', max_length=30)
    sex = forms.IntegerField(label='性別')
    age = forms.CharField(label='年齢', max_length=3)
    people = forms.IntegerField(label='人数')
    email = forms.EmailField(label='Mail')
    email_ch = forms.EmailField(label='Mail確認')
    tel_number = forms.CharField(label='携帯電話番号', max_length=15)
    objective = forms.CharField(label='目的', max_length=30)
    remarks = forms.CharField(label='備考', widget=forms.Textarea(), required=False)

