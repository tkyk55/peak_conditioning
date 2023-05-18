from django import forms


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    sex = forms.IntegerField(label='性別', required=False)
    phone = forms.CharField(max_length=5, label='電話', required=False)
    birthday = forms.DateTimeField(label='誕生日', required=False)
    image = forms.ImageField(required=False, )
