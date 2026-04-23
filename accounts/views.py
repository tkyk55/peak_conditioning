from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from accounts.models import CustomUser, Training
from accounts.forms import ProfileForm
from django.contrib.auth.mixins import LoginRequiredMixin
#from app.app_member.models import Staff

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
                'tel_number': user_data.tel_number,
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
        if 'profile_update' in request.POST and form.is_valid():
            user_data = CustomUser.objects.get(id=request.user.id)
            user_data.first_name = form.cleaned_data['first_name']
            user_data.last_name = form.cleaned_data['last_name']
            user_data.sex = form.cleaned_data['sex']
            user_data.tel_number = form.cleaned_data['tel_number']
            user_data.birthday = form.cleaned_data['birthday']
            if request.FILES.get('image'):
                user_data.image = request.FILES.get('image')
            user_data.save()
            return redirect('profile')
        else:
            # フォームが無効な場合の処理
            for field, errors in form.errors.items():
            #   # 各項目のエラーメッセージを取得
               for error in errors:
                  print(f"{field}: {error}")

        return render(request, 'accounts/profile.html', {
            'form': form
        })

class NippoView(TemplateView):
    def get(self, request, *args, **kwargs):

        return render(request, 'accounts/nippo-list.html', {
        })
