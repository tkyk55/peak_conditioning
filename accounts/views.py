from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from accounts.models import CustomUser, Training
from accounts.forms import ProfileForm
from django.contrib.auth.mixins import LoginRequiredMixin
from app.models import Staff

from datetime import datetime, date, timedelta, time

class ProfileView(View):
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)

        return render(request, 'accounts/profile.html', {
            'user_data': user_data,
        })

class ProfileEditView(View):
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)
        form = ProfileForm(
            request.POST or None,
            initial={
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'sex': user_data.sex,
                'phone1': user_data.phone1,
                'phone2': user_data.phone2,
                'phone3': user_data.phone3,
                'birthday': user_data.birthday,
                'image': user_data.image
            }
        )

        return render(request, 'accounts/profile_edit.html', {
            'form': form,
            'user_data': user_data
        })

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST or None)
        if form.is_valid():
            user_data = CustomUser.objects.get(id=request.user.id)
            user_data.first_name = form.cleaned_data['first_name']
            user_data.last_name = form.cleaned_data['last_name']
            user_data.sex = form.cleaned_data['sex']
            user_data.phone1 = form.cleaned_data['phone']
            user_data.birthday = form.cleaned_data['birthday']
            if request.FILES.get('image'):
                user_data.image = request.FILES.get('image')
            user_data.save()
            return redirect('profile')

        return render(request, 'accounts/profile.html', {
            'form': form
        })

class MenuView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)
        if Staff.objects.filter(user_id=request.user.id).exists():
             start_date = date.today()
             weekday = start_date.weekday()
             # カレンダー日曜日開始
             if weekday != 6:
                 start_date = start_date - timedelta(days=weekday + 1)
             return redirect('staff_calendar', start_date.year, start_date.month, start_date.day)

        staff_data = Staff.objects.filter(user_id=request.user.id)

        return render(request, 'accounts/menu.html', {
            'staff_data': staff_data
        })


class ReserveView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        Training_data = Training.objects.filter(experience_flg=0)

        return render(request, 'accounts/reserve.html', {
            'training_data': Training_data,
        })