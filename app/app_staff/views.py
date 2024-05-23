import calendar, json, pytz

from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.app_staff.models import Staff, Notification, StaffWork, ClosingDay
from app.app_member.models import Booking
from accounts.models import Training, CustomUser
from datetime import datetime, date, timedelta, time
from django.db.models import Q, Count, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth, TruncYear
from django.utils.timezone import localtime, make_aware
from app.app_staff.forms import MemberSearchForm, MemberForm, NotificationForm, StaffInputForm, StaffWorkInputForm, \
    StaffBookingInputForm, StaffClosingInputForm
from dateutil.relativedelta import relativedelta
from django.db import connection


class IndexView(TemplateView):
    template_name = 'app/index.html'


class StaffView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        staffs = Staff.objects.all()

        return render(request, 'app/staff.html', {
            'staffs': staffs,
        })


class StaffCalendarView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')

        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        # 日付変換関数呼び出し
        day_start_end = day_start_end_setting__function(year, month, day)
        start_date = day_start_end['start_date']  # 2024/1/1
        last_day = day_start_end['last_day']  # 31日

        days = days_today_setting_function(start_date, last_day, today)

        # スタッフデータ
        # staffall = Staff.objects.all() # 旧
        staffs = Staff.objects.filter(is_active=True)
        staff_cnt = Staff.objects.filter(is_active=True).count()

        # スタッフデータの側を作成
        calendar_data = {}
        for staff in staffs:
            # タイムテーブル作成
            timetable = {}
            # 9時～19時
            for hour in range(9, 20):
                row = {}
                for minute in [0, 15, 30, 45]:
                    row[minute] = 0
                timetable[hour] = row
            calendar_data[staff] = timetable

        datetime_start = day_start_end['today_j']
        datetime_end = datetime_start + timedelta(hours=23)
        ## staff_workデータベースアクセス
        staff_work_data = StaffWork.objects.filter(start__gte=datetime_start, end__lte=datetime_end)

        for staff_calendar in calendar_data:
            for hour_calendar in calendar_data[staff_calendar]:
                for minute_calendar in calendar_data[staff_calendar][hour_calendar]:

                    datetime_calendar = hour_minute_second__function(today, str(hour_calendar), str(minute_calendar), "00")

                    ## 15分後を算出
                    re_val = later_15minute__function(minute_calendar, hour_calendar)

                    datetime_calendar_end = make_aware(
                        datetime(year=datetime_start.year, month=datetime_start.month, day=datetime_start.day,
                                 hour=re_val['hour_end'], minute=re_val['minute_end']))

                    for staff_work in staff_work_data:
                        if staff_work.staff_id_id == staff_calendar.id and datetime_calendar < staff_work.end and datetime_calendar_end > staff_work.start:
                            calendar_data[staff_calendar][hour_calendar][minute_calendar] = 1  # 勤務中

        # トレーニングデータ取得
        training_data = Training.objects.filter(del_flg=0).order_by('display_num')

        start_date_j = day_start_end['start_date_j']
        end_date_j = day_start_end['end_date_j']

        # bookings クエリセットを取得する
        bookings = Booking.objects.filter(start__gte=start_date_j, end__lte=end_date_j, del_flg=0).order_by(
            'training_no')

        # bookingデータ編集
        booking_results = booking_results__function(bookings, 0)

        # トレーニング側作成
        training_detail = training_detail__function(training_data)

        # 休館日・ブロック取得
        bg_data = ClosingDay.objects.filter(start__gte=start_date_j, start__lte=end_date_j)

        # トレーニングデータ埋め込み
        training_detail = training_detail_make__function(training_detail, booking_results, today, bg_data)

        return render(request, 'app/staff_calendar.html', {
            'days': days,
            'before_day': today - timedelta(days=1),
            'next_day': today + timedelta(days=1),
            'before_month': min(days.keys()) - relativedelta(months=1),
            'next_month': max(days.keys()) + timedelta(days=1),
            'year': year,
            'month': month,
            'day': day,
            'today': today,
            'staffs': staffs,
            'staff_cnt': staff_cnt,
            'staff_calendar': calendar_data,
            'timetable': timetable__function(),
            'training_data': training_data,
            'training': training_detail,
        })


class StaffMemberView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        form = MemberSearchForm(request.POST or None)

        return render(request, 'app/member.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        # post_list = request.POST.getlist  # <input type="checkbox" name="delete"のnameに対応
        post_list_json = json.dumps(request.POST)
        request.session['post_list'] = post_list_json

        if 'pass_prm' in request.session:
            del request.session['pass_prm']

        return redirect('member_list')


class StaffMemberListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        serach_val = request.session.get('post_list')
        user_detail = member_serach_list__function(serach_val)

        return render(request, 'app/member_list.html', {
            'user_detail': user_detail,
        })

    def post(self, request, *args, **kwargs):
        post_pks = request.POST.getlist('select_user')  # <input type="checkbox" name="select_user"のvalueを取得

        # 選択していた場合は、編集画面に遷移し、何も選択されていない場合は同じ内容を描画する
        if post_pks:
            request.session['user_pk'] = post_pks  # セッションにセット
            return redirect('member_input')
        else:
            serach_val = request.session.get('post_list')
            user_detail = member_serach_list__function(serach_val)

            return render(request, 'app/member_list.html', {
                'user_detail': user_detail,
            })


class StaffMemberInputView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        user_pk = int(request.session.get('user_pk')[0])  # セッションからuserのid番号を引き継ぐ
        user_data = CustomUser.objects.get(id=user_pk)
        pass_val = request.session.get('pass_prm')

        if (pass_val):
            return redirect('staff_booking_input', pass_val['training_id'], 0, user_pk, 0, pass_val['year'],
                            pass_val['month'], pass_val['day'], pass_val['hour'], pass_val['minute'])
        else:
            form = MemberForm(
                request.POST or None,
                initial={
                    'member_no': user_data.member_no,
                    'first_name': user_data.first_name,
                    'last_name': user_data.last_name,
                    'sex': user_data.sex,
                    'birthday': user_data.birthday,
                    'email': user_data.email,
                    'tel_number': user_data.tel_number,
                    'num_contracts': user_data.num_contracts,
                    'stat_date': user_data.stat_date,
                    'end_date': user_data.end_date,
                    'is_shoes_custody': user_data.is_shoes_custody,
                    'amount_money': user_data.amount_money,
                    'memo': user_data.memo
                }
            )
            return render(request, 'app/member_input.html', {
                'form': form,
                'user_data': user_data
            })

    def post(self, request, *args, **kwargs):
        user_pk = request.POST.getlist('user_pk')  # <input type="checkbox" name="select_user"のvalueを取得
        form = MemberForm(request.POST or None)
        user_data = CustomUser.objects.get(id=user_pk[0])
        pass_val = request.session.get('pass_prm')

        if form.is_valid():
            user_data.member_no = form.cleaned_data['member_no']
            user_data.first_name = form.cleaned_data['first_name']
            user_data.last_name = form.cleaned_data['last_name']
            user_data.sex = form.cleaned_data['sex']
            user_data.birthday = form.cleaned_data['birthday']
            user_data.email = form.cleaned_data['email']
            user_data.tel_number = form.cleaned_data['tel_number']
            user_data.num_contracts = form.cleaned_data['num_contracts']
            user_data.stat_date = form.cleaned_data['stat_date']
            user_data.end_date = form.cleaned_data['end_date']
            user_data.is_shoes_custody = form.cleaned_data['is_shoes_custody']
            user_data.is_active = form.cleaned_data['is_active']
            user_data.amount_money = form.cleaned_data['amount_money']
            user_data.memo = form.cleaned_data['memo']
            user_data.save()
            return redirect('member_input')
        else:
            # フォームが無効な場合の処理
            # for field, errors in form.errors.items():
            #   # 各項目のエラーメッセージを取得
            #   for error in errors:
            #     print(f"{field}: {error}")

            return render(request, 'app/member_input.html', {
                'form': form,
                'user_data': user_data,
            })


class StaffNotificationView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        notification = Notification.objects.all()
        form = NotificationForm(
            request.POST or None,
            initial={
                'notice': notification.values('notice')[0]['notice']
            }
        )

        today = date.today()
        return render(request, 'app/notification.html', {
            'form': form,
            'today': today
        })

    def post(self, request, *args, **kwargs):
        form = NotificationForm(request.POST or None)
        if form.is_valid():
            notification = Notification.objects.get(id=1)
            notification.notice = form.cleaned_data['notice']
            notification.save()
            return redirect('notification')

        return redirect('member')


class StaffMenuView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        staffs = Staff.objects.all()

        return render(request, 'app/staff_menu.html', {
            'staffs': staffs,
        })

    def post(self, request, *args, **kwargs):
        staff_pk = request.POST.getlist('select_staff')  # <input type="checkbox" name="select_staff"のvalueを取得
        staffs = Staff.objects.all()
        submit_type = request.POST.getlist('submit')[0]

        if submit_type == '編集する':
            request.session['staff_pk'] = staff_pk[0]

            return redirect('staff_input')
        else:
            request.session['staff_pk'] = None
            return redirect('staff_input')


class StaffInputView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        staff_pk = request.session.get('staff_pk')

        if staff_pk is not None:  # staff_pkがNoneでない場合にインデックスアクセスを行う
            staff_pk_int = int(request.session.get('staff_pk'))
            staff_data = Staff.objects.get(id=staff_pk_int)
            request.session.pop('staff_pk', None)  # セッションを初期化しておく

            form = StaffInputForm(
                request.POST or None,
                initial={
                    'first_name': staff_data.first_name,
                    'last_name': staff_data.last_name,
                    'memo': staff_data.memo,
                    'is_active': staff_data.is_active
                }
            )
        else:
            form = StaffInputForm(request.POST or None)
            staff_pk_int = None

        return render(request, 'app/staff_input.html', {
            'form': form,
            'staff_pk': staff_pk_int,
        })

    def post(self, request, *args, **kwargs):
        form = StaffInputForm(request.POST or None)

        if form.is_valid():
            staff_pk = request.POST.getlist('staff_pk')  # <input type="hidden" name="staff_pk"のvalueを取得
            if staff_pk:  # スタッフ更新
                staff = Staff.objects.get(id=int(staff_pk[0]))
                staff.is_active = form.cleaned_data['is_active']
            else:  # スタッフ新規
                staff = Staff()
                staff.is_active = True
            staff.first_name = form.cleaned_data['first_name']
            staff.last_name = form.cleaned_data['last_name']
            staff.memo = form.cleaned_data['memo']
            staff.save()

            if staff_pk:  # スタッフ更新
                staff_pk = staff_pk[0]
            else:
                staff_data = Staff.objects.latest('id')
                staff_pk = staff_data.id

            request.session['staff_pk'] = staff_pk
            return redirect('staff_input')


class StaffListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        staffs = Staff.objects.all()

        return render(request, 'app/staff_list.html', {
            'staffs': staffs,
        })


class StaffWorkInputView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')

        # スタッフデータの側を作成
        staff_calendar = timetable__function()

        # 今日の設定
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        # クリックした日時がすでに登録されているかを探す
        day_start_end = day_start_end_setting__function(year, month, day)
        datetime_start_click = day_start_end['today_j']
        date_start = datetime_start_click.strftime('%Y-%m-%d')
        datetime_end = datetime_start_click + timedelta(hours=23)

        ## staff_workデータベースアクセス
        staff_time_data = StaffWork.objects.filter(staff_id=self.kwargs['id'], start__gte=datetime_start_click, end__lte=datetime_end)

        staff_time_data_id = None

        # すでに登録されていたら、登録時間をセット。そうでなければクリック時間を開始時間にセットし、開始時間の１時間後を終了時間にセットする
        if staff_time_data:
            datetime_staff_start = staff_time_data.values('start')[0]['start']
            datetime_staff_end = staff_time_data.values('end')[0]['end']

            for hour_calendar in staff_calendar:
                for minute_calendar in staff_calendar[hour_calendar]:
                    datetime_calendar = hour_minute_second__function(today, str(hour_calendar), str(minute_calendar), "00")

                    ## 15分後を算出
                    re_val = later_15minute__function(minute_calendar, hour_calendar)
                    datetime_calendar_end = hour_minute_second__function(today, str(re_val['hour_end']), str(re_val['minute_end']), "00")

                    if datetime_calendar < datetime_staff_end and datetime_calendar_end > datetime_staff_start:
                        staff_calendar[hour_calendar][minute_calendar] = 1  # 勤務中 html >> staff_work == 1
                        staff_time_data_id = staff_time_data.values('id')[0]['id']

        else:
            datetime_staff_start = hour_minute_second__function(today, str(self.kwargs['hour']), str(self.kwargs['minute']), "00")
            datetime_staff_end = datetime_staff_start + timedelta(hours=1)

        staff_name_data = Staff.objects.filter(id=self.kwargs['id'])

        form = StaffWorkInputForm(
            request.POST or None,
            initial={
                'start': datetime_staff_start,
                'end': datetime_staff_end,
            }
        )

        return render(request, 'app/staff_work_input.html', {
            'staff': staff_name_data,
            'form': form,
            'target_date': date_start,
            'timetable': timetable__function(),
            'staff_calendar': staff_calendar,
            'staff_time_data_id': staff_time_data_id,
            'today': today,
        })

    def post(self, request, *args, **kwargs):

        form = StaffWorkInputForm(request.POST or None)
        submit_type = request.POST.getlist('submit')[0]
        staff_id = request.POST.getlist('staff_id')  # <input type="hidden" name="staff_id"のvalueを取得
        staff_work_id = request.POST.getlist('staff_work_id')  # <input type="hidden" name="staff_work_id"のvalueを取得

        if submit_type == '削除':
            staffwork = StaffWork.objects.get(id=int(staff_work_id[0]))
            staffwork.delete()
            return redirect('menu')

        if form.is_valid():
            # postデータを展開
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']

            # postされた日付データがあるかを探して、あれば削除
            re_val = day_start_end_setting__function(start.year, start.month, start.day)
            datetime_start = re_val['today_j']
            re_val = day_start_end_setting__function(end.year, end.month, end.day)
            datetime_end = re_val['today_j']

            staffwork = StaffWork.objects.filter(staff_id_id=int(staff_id[0]), start__gte=datetime_start, end__lte=datetime_end)
            ## 削除判定
            if (staffwork):
                staffwork.delete()
            ## データ登録
            staffwork = StaffWork()
            staffwork.staff_id_id = int(staff_id[0])
            staffwork.start = start
            staffwork.end = end
            staffwork.save()

        # else:
        # フォームが無効な場合の処理
        # for field, errors in form.errors.items():
        #   # 各項目のエラーメッセージを取得
        #   for error in errors:
        #     print(f"{field}: {error}")

        return redirect('menu')


class StaffBookingInputView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        my_training_id = self.kwargs.get('training_id')
        my_booking_id = self.kwargs.get('booking_id')
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')
        user_id = self.kwargs.get('user_id')
        user_data = None
        if user_id:
            user_data = CustomUser.objects.get(id=int(user_id))

        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()
        day_start_end = day_start_end_setting__function(year, month, day)
        start_date = day_start_end['today_j']
        end_date = day_start_end['end_date_j']
        start = hour_minute_second__function(today, str(hour), str(minute), "00")
        end = start + timedelta(hours=1)

        # エラーメッセージ設定
        err_cd = self.kwargs.get('err_cd')
        err_msg = None
        if err_cd:
            err_msg = err_setting_function(err_cd)

        # トレーニングデータ取得
        training_data = Training.objects.filter(id=my_training_id, del_flg=0).order_by('display_num')

        # bookings クエリセットを取得する
        bookings = Booking.objects.filter(start__gte=start_date, end__lte=end_date, del_flg=0).order_by('training_no')

        # bookingデータ編集
        booking_results = booking_results__function(bookings, my_booking_id)

        # トレーニング側作成
        training_detail = training_detail__function(training_data)

        # 休館日・ブロック取得
        bg_data = ClosingDay.objects.filter(start__gte=day_start_end['start_date_j'], start__lte=day_start_end['end_date_j'])

        # トレーニングデータ埋め込み
        training_detail = training_detail_make__function(training_detail, booking_results, today, bg_data)

        # formの埋め込み
        booking_id = None
        booking_start = None
        booking_end = None
        booking_training_no = None
        booking_member_first_name = None
        booking_member_last_name = None

        for bookings in booking_results:
            if bookings['this_booking_flg'] == 1:
                booking_id = bookings['booking_id']
                booking_start = bookings['booking_start']
                booking_end = bookings['booking_end']
                booking_training_no = bookings['booking_training_no']
                booking_member_first_name = bookings['first_name']
                booking_member_last_name = bookings['last_name']

        if user_id:
            form = StaffBookingInputForm(
                request.POST or None,
                initial={
                    'booking_id': None,
                    'start': start if start else None,
                    'end': end if end else None,
                    'training_no': None,
                }
            )
        else:
            form = StaffBookingInputForm(
                request.POST or None,
                initial={
                    'booking_id': booking_id,
                    'start': booking_start.strftime('%Y-%m-%d %H:%M:%S') if booking_start else None,
                    'end': booking_end.strftime('%Y-%m-%d %H:%M:%S') if booking_end else None,
                    'training_no': booking_training_no,
                }
            )

        booking_member_name = booking_member_first_name or ""
        booking_member_name += booking_member_last_name or ""

        if booking_training_no:
            booking_training_no += 1

        return render(request, 'app/staff_booking_input.html', {
            'year': year,
            'month': month,
            'day': day,
            'today': today,
            'timetable': timetable__function,
            'training': training_detail,
            'training_data': training_data,
            'form': form,
            'booking_training_no': booking_training_no,
            'booking_member_name': booking_member_name,
            'select_user': user_data,
            'err_msg': err_msg,
        })

    def post(self, request, *args, **kwargs):
        form = StaffBookingInputForm(request.POST or None)
        my_training_id = self.kwargs.get('training_id')
        my_booking_id = self.kwargs.get('booking_id')
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')
        user_pk = None
        if request.session.get('user_pk'):
            user_pk = int(request.session.get('user_pk')[0])
        submit_type = request.POST.getlist('submit')[0]

        # 今日の設定
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        start_date = day_start_end['today_j']
        end_date = day_start_end['end_date_j']

        # トレーニングデータ取得
        training_data = Training.objects.filter(id=my_training_id, del_flg=0).order_by('display_num')

        # bookings クエリセットを取得する
        bookings = Booking.objects.filter(start__gte=start_date, end__lte=end_date, del_flg=0).order_by('training_no')

        # bookingデータ編集
        booking_results = booking_results__function(bookings, my_booking_id)

        # トレーニング側作成
        training_detail = training_detail__function(training_data)

        # 休館日・ブロック取得
        bg_data = ClosingDay.objects.filter(start__gte=day_start_end['start_date_j'], start__lte=day_start_end['end_date_j'])

        # トレーニングデータ埋め込み
        training_detail = training_detail_make__function(training_detail, booking_results, today, bg_data)

        if form.is_valid():
            if form.cleaned_data['booking_id']:
                booking_old_data = Booking.objects.get(id=int(form.cleaned_data['booking_id']))
            training_no = int(
                request.POST.getlist('training_no')[0]) - 1  # <input type="hidden" name="booking_id"のvalueを取得

            # 削除の場合
            if submit_type == '削除':
                booking = Booking()
                booking.id = form.cleaned_data['booking_id']
                booking.training = booking_old_data.training
                booking.user = booking_old_data.user
                booking.start = booking_old_data.start
                booking.end = booking_old_data.end
                booking.del_flg = 1
                booking.save()
                return redirect('menu')

            # 終了時間を開始時間の１時間後に定義
            start_end_time = form.cleaned_data['start'] + timedelta(hours=1)

            # 休館日重複チェック_black
            closing_exist_data = find_closing_exist_days__function('B', form.cleaned_data['start'], start_end_time,
                                                         my_training_id, None)
            if closing_exist_data and closing_exist_data[0].closing_type == 'B':
                err_cd = 10  # 選択した時間帯には黒ブロックが設定されているため、登録できません
                return redirect('staff_booking_input', my_training_id, my_training_id, user_pk, err_cd, year, month,
                                day, hour, minute)

            if closing_exist_data and closing_exist_data[0].closing_type == 'G' and closing_exist_data[
                0].training_no == training_no \
                    and closing_exist_data[0].start == form.cleaned_data['start'] and closing_exist_data[
                0].end == start_end_time:
                err_cd = 20  # 選択した時間帯には灰ブロックが設定されているため、登録できません
                return redirect('staff_booking_input', my_training_id, my_training_id, user_pk, err_cd, year, month,
                                day, hour, minute)

            # 重複チェック
            if form.cleaned_data['booking_id']:
                booking_exist_data = Booking.objects.filter(start__gte=form.cleaned_data['start'],
                                                            start__lt=start_end_time,
                                                            training=booking_old_data.training, training_no=training_no,
                                                            del_flg=0)
            else:
                booking_exist_data = Booking.objects.filter(start__gte=form.cleaned_data['start'],
                                                            start__lt=start_end_time, training=my_training_id,
                                                            training_no=training_no, del_flg=0)

            if (booking_exist_data):
                err_cd = 50  # 選択した時間帯には既に予約があるため、登録できません
                return redirect('staff_booking_input', my_training_id, my_training_id, user_pk, err_cd, year, month,
                                day, hour, minute)

            else:
                if form.cleaned_data['booking_id']:
                    booking = Booking()
                    booking.id = form.cleaned_data['booking_id']
                    booking.training = booking_old_data.training
                    booking.user = booking_old_data.user
                    booking.start = form.cleaned_data['start']
                    booking.end = form.cleaned_data['start'] + timedelta(hours=1)
                    booking.training_no = training_no
                    booking.save()
                    return redirect('menu')
                else:
                    booking = Booking()
                    booking.training = Training.objects.get(id=my_training_id)
                    booking.user = CustomUser.objects.get(id=user_pk)
                    booking.start = form.cleaned_data['start']
                    booking.end = form.cleaned_data['start'] + timedelta(hours=1)
                    booking.training_no = training_no
                    booking.save()
                    return redirect('menu')

        # else:
        # フォームが無効な場合の処理
        # for field, errors in form.errors.items():
        #   # 各項目のエラーメッセージを取得
        #    for error in errors:
        #      print(f"{field}: {error}")


class StaffBookingInputSearchView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        form = MemberSearchForm(request.POST or None)

        return render(request, 'app/member.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        training_id = self.kwargs.get('training_id')
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')

        pass_prm = {'training_id': training_id, 'year': year, 'month': month, 'day': day, 'hour': hour,
                    'minute': minute}

        post_list_json = json.dumps(request.POST)
        request.session['post_list'] = post_list_json
        request.session['pass_prm'] = pass_prm
        return redirect('member_list')


class StaffClosingDayView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        err_cd = self.kwargs.get('err_cd')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        # 今日の設定
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        start_date = day_start_end['today_j']
        first_date = day_start_end['start_date_j']
        last_day = day_start_end['last_day']
        target_date = start_date.strftime('%Y-%m-%d')

        days = days_today_setting_function(first_date, last_day, start_date)
        start_day = day_start_end['start_date_j']
        end_day = day_start_end['end_date_j']
        closing_data_all = ClosingDay.objects.filter(start__gte=day_start_end['start_date_j'], start__lte=day_start_end['end_date_j'], closing_type='C')

        # 日付データ加工
        days_data = {day: find_closing_day__function(day, closing_data_all) for day in days}

        # blockをクリックしたときのURLパラメータを取得
        closing_id_p = self.kwargs.get('closing_id')

        # ハイフンを押したときのURLパラメータを取得
        blackgray = self.kwargs.get('blackgray')
        click_training_id = self.kwargs.get('training_id')

        # 休館日クリックイベント
        year_p = self.kwargs.get('year')
        if year_p and err_cd is None and closing_id_p is None and blackgray is None:
            closing = self.kwargs.get('closing')
            closing_data = ClosingDay.objects.filter(start=start_date, closing_type='C')

            if closing == 'off' and closing_data:
                closing_data.delete()
                return redirect('staff_closing_day', year, month, day)
            elif closing == 'on' and not closing_data:
                closing_data = ClosingDay()
                closing_data.closing_type = 'C'
                closing_data.start = start_date
                closing_data.end = start_date
                closing_data.save()
                return redirect('staff_closing_day', year, month, day)
            # closing がない場合（日付クリック時）は下記処理を続行

        # <ブロック設定>
        # トレーニングデータ取得
        training_data = Training.objects.filter(del_flg=0).order_by('display_num')

        # トレーニング側作成
        training_detail = training_detail__function(training_data)

        # 休館日・ブロック取得
        bg_data = ClosingDay.objects.filter(start__gte=start_day, start__lte=end_day)

        # トレーニング側に休日埋め込み
        training_detail = training_detail_make__function(training_detail, None, today, bg_data)

        # formの埋め込み
        closing_id = None
        training = None
        training_no = None
        closing_type = None

        # ブロックがない時間（ハイフン）がクリックされたとき、フォームにその時間をセットする
        if (blackgray):
            datetime_start = hour_minute_second__function(today, str(hour), str(minute), "00")
            datetime_end = datetime_start + timedelta(hours=1)
        else:  # 初期表示時は黒ブロックの９時をセットする
            datetime_start = hour_minute_second__function(today, str("09"), str("00"), "00")
            datetime_end = datetime_start + timedelta(hours=1)

        # ブロックをクリックしたときは、formに値をセット
        closing_exist_data = ClosingDay.objects.filter(id=closing_id_p)
        if closing_id_p and closing_exist_data:
            closing_id = closing_exist_data.values('id')[0]['id']
            datetime_start = closing_exist_data.values('start')[0]['start']
            datetime_end = closing_exist_data.values('end')[0]['end']
            training = closing_exist_data.values('training')[0]['training']
            click_training_id = training
            training_no = 0
            if closing_exist_data.values('training_no'):
                temp_training_no = closing_exist_data.values('training_no')[0]['training_no']
                if temp_training_no is not None:
                    training_no = int(temp_training_no)
            closing_type = closing_exist_data.values('closing_type')[0]['closing_type']

        form = StaffClosingInputForm(
            request.POST or None,
            initial={
                'closing_id': closing_id,
                'start': datetime_start,
                'end': datetime_end,
                'training': training,
                'training_no': training_no,
                'closing_type': closing_type,
            }
        )

        return render(request, 'app/staff_closing_day.html', {
            'form': form,
            'days': days,
            'days_data': days_data,
            'start_day': start_day,
            'end_day': end_day,
            'before_day': today - timedelta(days=1),
            'next_day': today + timedelta(days=1),
            'before_month': min(days.keys()) - relativedelta(months=1),
            'next_month': max(days.keys()) + timedelta(days=1),
            'year': today.year,
            'month': today.month,
            'day_t': today.day,
            'today': today,
            'target_date': target_date,
            'timetable': timetable__function,
            'training': training_detail,
            'training_data': training_data,
            'err_cd': err_cd,
            'closing_exist_data': closing_exist_data,
            'click_training_id': click_training_id,
        })

    def post(self, request, *args, **kwargs):
        form = StaffBookingInputForm(request.POST or None)
        closing_type = request.POST.getlist('closing_type')[0]
        training_id = request.POST.getlist('training_id')[0]  # <input type="hidden" name="training_id"のvalueを取得
        #training_no = int(request.POST.getlist('training_no')[0]) - 1  # <input type="hidden" name="training_no"のvalueを取得
        closing_id = request.POST.getlist('closing_id')
        today_str = (request.POST.getlist('target_date')[0])
        today = datetime.strptime(today_str, '%Y-%m-%d')
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')

        # 削除ボタンが押された場合
        del_closing = request.POST.getlist('closeDel')
        if del_closing:
            closingday = ClosingDay.objects.filter(id=del_closing[0])
            closingday.delete()
            return redirect('staff_closing_day', year, month, day)

        if form.is_valid():
            # postデータを展開
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']

            # 休館日重複チェック
            closing_exist_data = find_closing_exist_days__function(closing_type, start, end, training_id, None)

            if closing_exist_data:
                err_cd = 99
                return redirect('staff_closing_day', err_cd, closing_type, today.year, today.month, today.day,
                                start.hour, start.minute)
            else:
                if closing_id:
                    closingday = ClosingDay.objects.filter(id=closing_id)
                    closingday.delete()
                    closingday = ClosingDay()
                    closingday.closing_type = closing_type
                    closingday.start = start
                    closingday.end = end
                    closingday.training_id = training_id
                    #if closing_type == 'G':
                    #    closingday.training_no = training_no
                    closingday.save()
                else:
                    closingday = ClosingDay()
                    closingday.closing_type = closing_type
                    closingday.start = start
                    closingday.end = end
                    closingday.training_id = training_id
                    #if closing_type == 'G':
                    #    closingday.training_no = training_no
                    closingday.save()

            return redirect('staff_closing_day', year, month, day)


class StaffPersonalView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        start_date = day_start_end['start_date']  # 2024/1/1
        last_day = day_start_end['last_day']  # 31日
        days = days_today_setting_function(start_date, last_day, today)
        before_month = min(days.keys()) - relativedelta(months=13),

        ### MySQL 5.7以上 で構築できるならばこのロジックを使用すること
        # booking_data = Booking.objects.filter(start__gte=before_month)
        # booking_data = booking_data.annotate(month=ExtractMonth('start'), year=ExtractYear('start'))
        # booking_data = booking_data.values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

        ### MySQL 5.7以上が使える場合はSQLで抽出するロジックは削除すること
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT YEAR(start) as year, MONTH(start) as month, COUNT(id) as total
                FROM app_member_booking
                WHERE start >= %s and training_id = 6
                GROUP BY YEAR(start), MONTH(start)
                ORDER BY year, month desc
            """, [before_month])
            results = cursor.fetchall()

        return render(request, 'app/staff_personal.html', {
            'results': results
        })

    def post(self, request, *args, **kwargs):
        return redirect('menu')


class StaffSemiPersonalView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        start_date = day_start_end['start_date']  # 2024/1/1
        last_day = day_start_end['last_day']  # 31日
        days = days_today_setting_function(start_date, last_day, today)
        before_month = min(days.keys()) - relativedelta(months=13),

        ### MySQL 5.7以上 で構築できるならばこのロジックを使用すること
        # booking_data = Booking.objects.filter(start__gte=before_month)
        # booking_data = booking_data.annotate(month=ExtractMonth('start'), year=ExtractYear('start'))
        # booking_data = booking_data.values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

        ### MySQL 5.7以上が使える場合はSQLで抽出するロジックは削除すること
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT YEAR(start) as year, MONTH(start) as month, COUNT(id) as total
                FROM app_member_booking
                WHERE start >= %s and training_id = 1
                GROUP BY YEAR(start), MONTH(start)
                ORDER BY year, month desc
            """, [before_month])
            results = cursor.fetchall()

        return render(request, 'app/staff_semi_personal.html', {
            'results': results
        })

    def post(self, request, *args, **kwargs):
        return redirect('menu')


class StaffExReserveView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        start_date = day_start_end['start_date']  # 2024/1/1
        last_day = day_start_end['last_day']  # 31日
        days = days_today_setting_function(start_date, last_day, today)
        before_month = min(days.keys()) - relativedelta(months=13),

        #datetime_start = re_val['start_day_p_j']
        ### MySQL 5.7以上 で構築できるならばこのロジックを使用すること
        # booking_data = Booking.objects.filter(start__gte=datetime_start)
        # booking_data = booking_data.annotate(month=ExtractMonth('start'), year=ExtractYear('start'))
        # booking_data = booking_data.values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

        ### MySQL 5.7以上が使える場合はSQLで抽出するロジックは削除すること
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT YEAR(start) as year, MONTH(start) as month, count(if( training_id = 4, id, null)) as ex_personal_cnt ,count(if( training_id = 5 , id, null)) as ex_semi_personal_cnt ,count(id) as total
                FROM app_member_exbooking
                WHERE start >= %s and (training_id = 4 or training_id = 5) 
                GROUP BY YEAR(start), MONTH(start)
                ORDER BY year, month desc
            """, [before_month])
            results = cursor.fetchall()

        return render(request, 'app/staff_ex_reserve_cnt.html', {
            'results': results
        })

    def post(self, request, *args, **kwargs):
        return redirect('menu')


class StaffWorkCntView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):

        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year:
            today = date(year=year, month=month, day=day)
        else:
            today = date.today()

        day_start_end = day_start_end_setting__function(today.year, today.month, today.day)
        datetime_start = day_start_end['start_date_j']
        datetime_end = day_start_end['end_date_j']
        start_date = day_start_end['start_date']
        last_day = day_start_end['last_day']
        days = days_today_setting_function(start_date, last_day, today)

        monthly_work_hours = StaffWork.objects.filter(
            start__gte=datetime_start,
            end__lte=datetime_end
        ).annotate(
            month=TruncMonth('start'),
            duration=ExpressionWrapper(F('end') - F('start'), output_field=fields.DurationField())
        ).values('month', 'staff_id').annotate(
            total_work_duration=Sum('duration')  # 秒単位で合計
        ).values('staff_id__first_name', 'staff_id__last_name', 'total_work_duration').order_by('staff_id')

        # Pythonレベルで時間に変換
        for work_hour in monthly_work_hours:
            work_hour['total_work_hours'] = work_hour['total_work_duration'].total_seconds() / 3600

        return render(request, 'app/staff_work_cnt.html', {
            'monthly_work_hours': monthly_work_hours,
            'before_month': min(days.keys()) - relativedelta(months=1),
            'next_month': max(days.keys()) + timedelta(days=1),
            'today': start_date,
        })

    def post(self, request, *args, **kwargs):
        return redirect('menu')


#################
# ---関数エリア---
#################

def timetable__function():
    # タイムテーブル作成
    timetable = {}
    # 9時～19時
    for hour in range(9, 20):
        row = {}
        for minute in [0, 15, 30, 45]:
            row[minute] = 0
        timetable[hour] = row

    return timetable


def training_detail__function(training_data):
    # 各トレーニングの出力情報を編集
    training_detail = {}
    for training in training_data:
        training_no = {}
        for duplicates_num in range(0, training.duplicates_num):
            #     # 9時～19時
            timetable = {}
            for hour in range(9, 20):
                row = {}
                for minute in [0, 15, 30, 45]:
                    row[minute] = {'skip_flg': 0, 'booking_id': '', 'name': '', 'training_id': '',
                                   'this_booking_flg': 0, 'blackgray': '', 'closing_id': ''}
                timetable[hour] = row
            training_no[duplicates_num] = timetable
        training_detail[training] = training_no

    return training_detail


def booking_results__function(bookings, my_booking_id):
    # bookingデータを編集
    booking_results = []
    # 結果を表示
    for booking in bookings:
        user = booking.user
        # 日本時間に変換
        booking_start_jst = booking.start.astimezone(pytz.timezone('Asia/Tokyo'))
        booking_end_jst = booking.end.astimezone(pytz.timezone('Asia/Tokyo'))

        this_booking_flg = 0
        if booking.id == my_booking_id:
            this_booking_flg = 1

        booking_results.append({
            'booking_id': booking.id,
            'booking_training_id': booking.training,
            'booking_training_no': booking.training_no,
            'booking_start': booking_start_jst,
            'booking_end': booking_end_jst,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'this_booking_flg': this_booking_flg
        })
    return booking_results


def training_detail_make__function(training_detail, booking_results, today, bg_data):
    japan_timezone = pytz.timezone('Asia/Tokyo')  # 日本のタイムゾーンを設定
    # トレーニングデータを埋め込む
    for training_name in training_detail:
        for training_no in training_detail[training_name]:
            booking_id_before = ''  # 直前のbooking_idを宣言
            for training_hour in training_detail[training_name][training_no]:
                for training_minute in training_detail[training_name][training_no][training_hour]:

                    # 時間を定義
                    str_type = str(today) + " " + str(training_hour) + ":" + str(training_minute) + ":00"
                    datetime_calendar = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')
                    datetime_calendar = japan_timezone.localize(datetime_calendar)

                    ## 15分後を算出
                    re_val = later_15minute__function(training_minute, training_hour)

                    datetime_calendar_end = make_aware(
                        datetime(year=today.year, month=today.month, day=today.day, hour=re_val['hour_end'],
                                 minute=re_val['minute_end']))

                    training_detail[training_name][training_no][training_hour][training_minute][
                        'training_id'] = training_name.id

                    if booking_results:
                        for training_data_r in booking_results:
                            if training_name == training_data_r['booking_training_id'] \
                                    and training_no == training_data_r['booking_training_no'] \
                                    and datetime_calendar < training_data_r['booking_end'] and datetime_calendar_end > \
                                    training_data_r['booking_start']:

                                # 直前のbooking_id を見る
                                if (booking_id_before == training_data_r['booking_id']):
                                    training_detail[training_name][training_no][training_hour][training_minute][
                                        'skip_flg'] = 1
                                else:
                                    training_detail[training_name][training_no][training_hour][training_minute][
                                        'skip_flg'] = 0
                                # 直前のbooking_idをセット
                                booking_id_before = training_data_r['booking_id']

                                training_detail[training_name][training_no][training_hour][training_minute][
                                    'booking_id'] = training_data_r['booking_id']
                                training_detail[training_name][training_no][training_hour][training_minute]['name'] = \
                                training_data_r['first_name'] + " " + training_data_r['last_name']
                                training_detail[training_name][training_no][training_hour][training_minute][
                                    'this_booking_flg'] = training_data_r['this_booking_flg']

                    if bg_data:
                        for bg_detail in bg_data:
                            # ブロックデータがある場合は埋め込み
                            if bg_detail.closing_type == 'B' and datetime_calendar < bg_detail.end and datetime_calendar_end > bg_detail.start \
                               and training_name.id == bg_detail.training.id:
                                   training_detail[training_name][training_no][training_hour][training_minute]['blackgray'] = bg_detail.closing_type
                                   training_detail[training_name][training_no][training_hour][training_minute]['closing_id'] = bg_detail.id
                            elif bg_detail.closing_type == 'G' and datetime_calendar < bg_detail.end and datetime_calendar_end > bg_detail.start \
                               and training_name.id == bg_detail.training.id:  #and training_no == bg_detail.training_no:  # 0始まりで格納（loop.counter考慮はDBではしない)
                                   training_detail[training_name][training_no][training_hour][training_minute]['blackgray'] = bg_detail.closing_type
                                   training_detail[training_name][training_no][training_hour][training_minute]['closing_id'] = bg_detail.id

                        # else:
                        #     # 直前のbooking_idをリセット
                        #     booking_id_before = ''

    return training_detail


def later_15minute__function(minute_calendar, hour_calendar):
    ## 15分後を算出
    if minute_calendar == 0 or minute_calendar == 15 or minute_calendar == 30:
        hour_end = hour_calendar
        minute_end = minute_calendar + 15
    else:
        hour_end = hour_calendar + 1
        minute_end = 0

    return {'hour_end': hour_end, 'minute_end': minute_end}


def member_serach_list__function(serach_val):
    serach_val_json = json.loads(serach_val)
    user_detail = ''
    if serach_val_json["member_no"]:
        user_detail = CustomUser.objects.filter(member_no__contains=serach_val_json["member_no"])
    if serach_val_json["first_name"]:
        user_detail_b = CustomUser.objects.filter(first_name__contains=serach_val_json["first_name"])
        if user_detail:
            user_detail = user_detail.union(user_detail_b)
        else:
            user_detail = user_detail_b
    if serach_val_json["last_name"]:
        user_detail_b = CustomUser.objects.filter(last_name__contains=serach_val_json["last_name"])
        if user_detail:
            user_detail = user_detail.union(user_detail_b)
        else:
            user_detail = user_detail_b
    if serach_val_json["tel_number"]:
        user_detail_b = CustomUser.objects.filter(tel_number__contains=serach_val_json["tel_number"])
        if user_detail:
            user_detail = user_detail.union(user_detail_b)
        else:
            user_detail = user_detail_b

    return (user_detail)


def find_closing_day__function(day, closing_data_all):
    japan_timezone = pytz.timezone('Asia/Tokyo')  # 日本のタイムゾーンを設定
    day_p = str(day.year) + "-" + str(day.month) + "-" + str(day.day) + " " + "00:00:00"
    day_ymd = datetime.strptime(day_p, '%Y-%m-%d %H:%M:%S')
    day_ymd_jp = japan_timezone.localize(day_ymd)

    for closing_day in closing_data_all:
        if day_ymd_jp == closing_day.start:
            return {'closing_day': 1}

    return {'closing_day': 0}


def find_closing_exist_days__function(closing_type, start, end, training_id, training_no):
    # 休館日検索
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


def hour_minute_second__function(date_data, hour, minute, second):
    japan_timezone = pytz.timezone('Asia/Tokyo')  # 日本のタイムゾーンを設定
    datetime_str = str(date_data) + " " + str(hour) + ":" + str(minute) + ":" + str(second)
    datetime_tmp = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    datetime_j = japan_timezone.localize(datetime_tmp)

    return datetime_j


def err_setting_function(err_cd):
    # エラーメッセージ編集
    err_msg = None
    if err_cd == 10:
        err_msg = '選択した時間帯には黒ブロックが設定されているため、登録できません(code_10)'
    elif err_cd == 20:
        err_msg = '選択した時間帯には灰ブロックが設定されているため、登録できません(code_20)'
    elif err_cd == 50:
        err_msg = '選択した時間帯には既に他の予約があるため、登録できません(code_50)'

    return err_msg


def days_today_setting_function(start_date, last_day, day_today):
    # 月末と今日をINNパラメータで受け取ると、今月の日付行列を今日フラグを立てて返す
    days = [start_date + timedelta(days=day) for day in range(last_day)]
    row = {}
    for days_data in days:
        if days_data == day_today:
            row[days_data] = {'today_flg': 1}
        else:
            row[days_data] = {'today_flg': 0}

    return row
