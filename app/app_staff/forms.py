from django import forms
from django.utils import timezone

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
    start = forms.DateTimeField(
        label='仕事開始時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_work'}),
    )
    end = forms.DateTimeField(
        label='仕事終了時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_work'}),
    )

class StaffBookingInputForm(forms.Form):
    booking_id = forms.IntegerField(label='予約ID' ,required=False)
    start = forms.DateTimeField(
        label='開始時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_booking'}),
    )
    end = forms.DateTimeField(
        label='終了時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_booking'}),
    )
    training_no = forms.IntegerField(label='トレーニングNo', required=False)

class StaffClosingInputForm(forms.Form):
    closing_id = forms.IntegerField(label='予約ID', required=False)
    start = forms.DateTimeField(
        label='開始時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_booking'}),
    )
    end = forms.DateTimeField(
        label='終了時間',
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control_staff_booking'}),
    )
    training_id = forms.IntegerField(label='トレーニングID', required=False)
    training_no = forms.IntegerField(label='トレーニングNo', required=False)

