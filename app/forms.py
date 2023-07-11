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


