from django import forms


class ProfileForm(forms.Form):
    GENDER_CHOICES = [
        ('0', '選択しない'),
        ('1', '男性'),
        ('2', '女性'),
    ]

    first_name = forms.CharField(max_length=30, label='姓')
    last_name = forms.CharField(max_length=30, label='名')
    sex = forms.ChoiceField(label='性別', choices=GENDER_CHOICES, required=True)
    tel_number = forms.CharField(max_length=13, label='電話', required=False)
    birthday = forms.DateField(widget=forms.DateInput(
        attrs={
            'type': 'date',
            'class': 'form-control_staff_booking'
        }
    ))
    image = forms.ImageField(required=False, )
