import calendar , json

from django.shortcuts import get_object_or_404, render ,redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.models import Staff, Booking, ExBooking, Master ,Notification
from accounts.models import Training ,CustomUser
from datetime import datetime, date, timedelta, time
from django.db.models import Q ,Count
from django.utils.timezone import localtime, make_aware
from app.forms import BookingForm, ExBookingForm, MemberSearchForm, MemberForm ,NotificationForm


class IndexView(TemplateView):
  template_name = 'app/index.html'

class StaffView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    staffs = Staff.objects.all()

    return render(request, 'app/staff.html', {
      'staffs': staffs,
    })

class CalendarView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = Training.objects.filter(id=self.kwargs['pk'])
    today = date.today()
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    duplicates_num = training_data.values('duplicates_num')[0]['duplicates_num']  # 予約可能数取得

    if year and month and day:
      # 週始め
      start_date = date(year=year, month=month, day=day)
    else:
      start_date = today
    # 1週間
    days = [start_date + timedelta(days=day) for day in range(7)]
    start_day = days[0]
    end_day = days[-1]

    calendar_ = {}
    # 9時～19時
    for hour in range(9, 20):
      mrow = {}
      for minute in [0,15,30,45]:
        row = {}
        for day in days:
          row[day] = 0  # 予約可
        mrow[minute] = row
      calendar_[hour] = mrow

    ### 予約状態を取得する
    start_time = make_aware(datetime.combine(start_day, time(hour=9, minute=0, second=0)))
    end_time = make_aware(datetime.combine(end_day, time(hour=19, minute=45, second=0)))
    booking_data = Booking.objects.filter(training__in=training_data).exclude(Q(start__gt=end_time) | Q(end__lt=start_time))

    # ユーザーデータ
    user_data = CustomUser.objects.filter(id=request.user.id)
    user_num_times = user_data.values('num_times')[0]['num_times']  # 予約残数
    user_stat_date = user_data.values('stat_date')[0]['stat_date']  # 契約開始
    user_end_date = user_data.values('end_date')[0]['end_date']  # 契約終了

    now_time = datetime.today()

    for hour_calendar in calendar_:
      for minute_calendar in calendar_[hour_calendar]:
        for day_calendar in calendar_[hour_calendar][minute_calendar]:

          arr_other_booking_cnt = {}
          arr_other_booking_cnt[0] = 0
          arr_other_booking_cnt[1] = 0
          arr_other_booking_cnt[2] = 0
          arr_other_booking_cnt[3] = 0

          # 45分前をセットする
          minute_calendar_before = minute_calendar
          hour_calendar_before = hour_calendar
          str_type = str(day_calendar) + " " + str(hour_calendar) + ":" + str(minute_calendar) + ":00"
          datetime_calender = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

          if minute_calendar == 0:
            minute_calendar_before = 15
            hour_calendar_before = hour_calendar_before - 1
          elif minute_calendar == 15:
            minute_calendar_before= 30
            hour_calendar_before = hour_calendar_before - 1
          elif minute_calendar == 30:
            minute_calendar_before = 45
            hour_calendar_before = hour_calendar_before - 1
          elif minute_calendar == 45:
            minute_calendar_before = 0

          str_type = str(day_calendar) + " " + str(hour_calendar_before) + ":" + str(minute_calendar_before) + ":00"
          datetime_calendar_before = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

          # その時間帯の予約数を数える
          for booking in booking_data:
            local_time = localtime(booking.start)
            booking_date = local_time.date()
            booking_hour = local_time.hour
            booking_minute = local_time.minute

            str_type = str(booking_date) + " " + str(booking_hour) + ":" + str(booking_minute) + ":00"
            datetime_booking = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

            if datetime_calendar_before <= datetime_booking and datetime_booking <= datetime_calender : # 45分遡って、予約があった場合数える
              if booking.user.id == request.user.id: # 自分の予約？
                calendar_[hour_calendar][minute_calendar][day_calendar] = 1  # 自分が「予約済み」
              else:
                arr_other_booking_cnt[0] = arr_other_booking_cnt[0] + 1

            if day_calendar == booking_date:
              if calendar_[hour_calendar][minute_calendar][day_calendar] != 1:  # 自分が「予約済み」
                 calendar_[hour_calendar][minute_calendar][day_calendar] = 7

          ## 45分後の予約時間まで掘り下げて、その１時間帯で予約が埋まっていたら「満席」：他人の場合 or 「予約不可」：自分が予約あった場合

          # 初期設定
          minute_calendar_after = minute_calendar
          hour_calendar_after = hour_calendar

          for other_booking in range(1,4):

            # 15分後をセットする
            if minute_calendar_after == 0 or minute_calendar_after == 15 or minute_calendar_after == 30:
              minute_calendar_after = minute_calendar_after + 15
            else:
              hour_calendar_after = hour_calendar_after + 1
              minute_calendar_after = 0

            str_type = str(day_calendar) + " " + str(hour_calendar_after) + ":" + str(minute_calendar_after) + ":00"
            datetime_calendar_after = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

            minute_calendar_before = minute_calendar_after
            hour_calendar_before = hour_calendar_after

            # 45分前をセットする
            if minute_calendar_after == 0:
              minute_calendar_before = 15
              hour_calendar_before = hour_calendar_before - 1
            elif minute_calendar_after == 15:
              minute_calendar_before= 30
              hour_calendar_before = hour_calendar_before - 1
            elif minute_calendar_after == 30:
              minute_calendar_before = 45
              hour_calendar_before = hour_calendar_before - 1
            elif minute_calendar_after == 45:
              minute_calendar_before = 0

            str_type = str(day_calendar) + " " + str(hour_calendar_before) + ":" + str(minute_calendar_before) + ":00"
            datetime_calendar_before = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

            # 予約を確認する
            for booking in booking_data:
              local_time = localtime(booking.start)
              booking_date = local_time.date()
              booking_hour = local_time.hour
              booking_minute = local_time.minute

              str_type = str(booking_date) + " " + str(booking_hour) + ":" + str(booking_minute) + ":00"
              datetime_booking = datetime.strptime(str_type, '%Y-%m-%d %H:%M:%S')

              if datetime_calendar_before <= datetime_booking and datetime_booking <= datetime_calendar_after: # 45分遡って、予約があった場合数える
                if booking.user.id == request.user.id: # 自分の予約？
                  if calendar_[hour_calendar][minute_calendar][day_calendar] != 1:
                    calendar_[hour_calendar][minute_calendar][day_calendar] = 3  # 自分が予約してるので「予約不可」
                else:
                  arr_other_booking_cnt[other_booking] = arr_other_booking_cnt[other_booking] + 1

          # 時間切れ
          now_time_one = now_time + timedelta(hours=1)
          if datetime_calender <= now_time_one:
            calendar_[hour_calendar][minute_calendar][day_calendar] = 99  # 時間切れ
          else:
            # その時間帯から45分後枠までの予約が重複数より上回るか判断。上回る場合満席
            if calendar_[hour_calendar][minute_calendar][day_calendar] != 1:
              if user_stat_date <= day_calendar and day_calendar <= user_end_date:
                if arr_other_booking_cnt[0] >= duplicates_num or arr_other_booking_cnt[1] >= duplicates_num or arr_other_booking_cnt[2] >= duplicates_num or arr_other_booking_cnt[3] >= duplicates_num:
                  calendar_[hour_calendar][minute_calendar][day_calendar] = 2  # 「満席」
                elif duplicates_num > 1 and (arr_other_booking_cnt[0] > 0 or arr_other_booking_cnt[1] > 1 or arr_other_booking_cnt[2] > 0 or arr_other_booking_cnt[3] > 0):
                  if user_num_times > 0:
                      calendar_[hour_calendar][minute_calendar][day_calendar] = 4  # 「残りわずか」
                  else:
                    calendar_[hour_calendar][minute_calendar][day_calendar] = 6  # 自分の予約残数がない「予約不可」
                elif user_num_times == 0:
                  calendar_[hour_calendar][minute_calendar][day_calendar] = 6  # 自分の予約残数がない「予約不可」
              else:
                calendar_[hour_calendar][minute_calendar][day_calendar] = 5  # 自分の契約期間外「予約不可」

    return render(request, 'app/calendar.html', {
       'training_data': training_data,
       'calendar': calendar_,
       'days': days,
       'start_day': start_day,
       'end_day': end_day,
       'before': days[0] - timedelta(days=7),
       'next': days[-1] + timedelta(days=1),
       'today': today,
    })


class BookingView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = Training.objects.filter(id=self.kwargs['pk'])
    user_data = CustomUser.objects.get(id=request.user.id)
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    hour = self.kwargs.get('hour')
    minute = self.kwargs.get('minute')
    form = BookingForm(request.POST or None)

    return render(request, 'app/booking.html', {
      'training_data': training_data,
      'user_data': user_data,
      'year': year,
      'month': month,
      'day': day,
      'hour': hour,
      'minute': minute,
      'form': form,
    })

  def post(self, request, *args, **kwargs):
    training_data = get_object_or_404(Training, id=self.kwargs['pk'])
    training_data_obj = Training.objects.filter(id=self.kwargs['pk'])
    user_data = get_object_or_404(CustomUser, id=request.user.id)
    user_detail = CustomUser.objects.filter(id=request.user.id)
    num_times = user_detail.values('num_times')[0]['num_times']

    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    hour = self.kwargs.get('hour')
    minute = self.kwargs.get('minute')
    if minute == 0:
       hour_end = hour
       minute_end = 45
    elif minute == 15:
       hour_end = hour +1
       minute_end = 0
    elif minute == 30:
       hour_end = hour +1
       minute_end = 15
    else:
       hour_end = hour +1
       minute_end = 30
    start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute))
    end_time = make_aware(datetime(year=year, month=month, day=day, hour=hour_end, minute=minute_end))

    duplicates_num = training_data_obj.values('duplicates_num')[0]['duplicates_num']  # 予約可能数取得
    booking_data = Booking.objects.filter(training=training_data, start=start_time)
    booking_count = Booking.objects.filter(training=training_data, start=start_time).count()  # 予約数
    form = BookingForm(request.POST or None)

    # ダブルブッキングチェック
    if duplicates_num == 0:
      if booking_data.exists():
        return render(request, 'app/booking_exists.html', {
          'training_data': training_data
        })
    if duplicates_num <= booking_count:
      return render(request, 'app/booking_exists.html', {
        'training_data': training_data
      })
    else:
      if form.is_valid():
        booking = Booking()
        booking.training = training_data
        booking.user = user_data
        booking.start = start_time
        booking.end = end_time
        booking.save()
        # 予約残数減数処理
        user_detail = CustomUser.objects.get(id=request.user.id)
        if num_times > 0 or num_times < 98:  # 0回または99回以上（サブスク）がセットされている場合は減数処理しない
          user_detail.num_times = num_times - 1
          user_detail.save()

        return render(request, 'app/thanks.html', {
          'training_data': training_data,
        })

    return render(request, 'app/booking.html', {
        'training_data': training_data,
        'user_data': user_data,
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute
      })

class ThanksView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = request.booking.training

    return render(request, 'app/thanks.html', {
      'training_data': training_data,
    })

class StaffCalendarView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    first_day = 1
    day = self.kwargs.get('day')
    today = date.today()
    start_date = date(year=year, month=month, day=first_day)
    last_day = calendar.monthrange(year=year, month=month)[1]
    next_month = date(year=year, month=month, day=last_day) + timedelta(days=1)
    days = [start_date + timedelta(days=day) for day in range(last_day)]
    start_day = days[0]
    end_day = date(year=year, month=month, day=last_day)

    # スタッフデータ
    staffs = user_data = CustomUser.objects.filter(is_staff=True)
    #print(staffs)
    staffall = Staff.objects.all()
    #print(staffall)
    staff_cnt = CustomUser.objects.filter(is_staff=True).count()
    #staff_cnt = Staff.objects.all().count()

    # タイムテーブル作成
    timetable = {}
    # 9時～19時
    for hour in range(9, 20):
      row = {}
      for minute in [0,15,30,45]:
        row[minute] = 0
      timetable[hour] = row

    # トレーニングデータ取得
    training_data = Training.objects.order_by('display_num')
    #print(training_data.values('duplicates_num')[0]['duplicates_num'])

    # 各トレーニングの出力情報を編集
    traning_detail = {}
    for training in training_data:
       row = {}

       for duplicates_num in range(0, training.duplicates_num):
         row[duplicates_num] = timetable
       traning_detail[training] = row

    return render(request, 'app/staff_calendar.html', {
        'days': days,
        'start_day': start_day,
        'end_day': end_day,
        'before_day': today - timedelta(days=1),
        'next_day': today + timedelta(days=1),
        'before_month': date(year=year, month=month-1, day=first_day),
        'next_month': days[-1] + timedelta(days=1),
        'year': year,
        'month': month,
        'day': day,
        'today': today,
        'staffs': staffall,
        'staff_cnt': staff_cnt,
        'timetable': timetable,
        'training': traning_detail,
        'training_data': training_data
      })

class MypageView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.filter(id=request.user.id)
    # 期間を算出
    user_stat_date = user_data.values('stat_date')[0]['stat_date']  # 契約開始
    user_end_date = user_data.values('end_date')[0]['end_date']  # 契約終了
    user_date_dif = user_end_date.month - user_stat_date.month

    # 過去の予約は出さないようにするため、現時間より前の予約は除外する
    start_time = datetime.today()
    booking_data = Booking.objects.filter(user=request.user.id).exclude(Q(end__lt=start_time))

    # training_category = <QuerySet [{'training': 1, 'training_cnt': 2}, {'training': 2, 'training_cnt': 1}]>
    training_category = booking_data.values('training').annotate(training_cnt=Count('training')).order_by('training')

    notification = Notification.objects.all()

    return render(request, 'app/mypage.html', {
        'user_data': user_data,
        'booking_data': booking_data,
        'training_category': training_category,
        'notification': notification,
        'user_date_dif': user_date_dif
      })

class CancelView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.get(id=request.user.id)

    # 過去の予約は出さないようにするため、現時間より前の予約は除外する
    start_time = datetime.today()
    booking_data = Booking.objects.filter(user=request.user.id).exclude(Q(end__lt=start_time))

    training_category = booking_data.values('training').annotate(training_cnt=Count('training')).order_by('training')

    return render(request, 'app/cancel.html', {
      'user_data': user_data,
      'booking_data': booking_data,
      'training_category': training_category
    })

  def post(self, request):
      post_pks = request.POST.getlist('delete')  # <input type="checkbox" name="delete"のnameに対応
      Booking.objects.filter(pk__in=post_pks).delete()
      user_data = CustomUser.objects.filter(id=request.user.id)
      num_times = user_data.values('num_times')[0]['num_times']
      user_detail = CustomUser.objects.get(id=request.user.id)
      if num_times < 98:  # 99回以上（サブスク考慮）がセットされている場合は加算処理しない
         user_detail.num_times = num_times + len(post_pks)
         user_detail.save()

      user_data = CustomUser.objects.get(id=request.user.id)
      booking_data = Booking.objects.filter(user=request.user.id)
      training_category = booking_data.values('training').annotate(training_cnt=Count('training')).order_by('training')

      return render(request, 'app/cancelok.html', {
        'user_data': user_data,
        'booking_data': booking_data,
        'training_category': training_category
      })

class ExReserveView(TemplateView):
  def get(self, request, *args, **kwargs):
    Training_data = Training.objects.filter(experience_flg=1)

    return render(request, 'app/ex_reserve.html', {
      'training_data': Training_data,
    })


class ExperienceView(TemplateView):
  def get(self, request, *args, **kwargs):
    # form = ProfileForm(
    #   request.POST or None,
    # )

    return render(request, 'app/experience.html', {
      # 'form': form,
      # 'user_data': user_data
    })

class ExCalendarView(TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = Training.objects.filter(id=self.kwargs['pk'])
    today = date.today()
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    if year and month and day:
      # 週始め
      start_date = date(year=year, month=month, day=day)
    else:
      start_date = today
    # 1週間
    days = [start_date + timedelta(days=day) for day in range(7)]
    start_day = days[0]
    end_day = days[-1]

    calendar_ = {}
    # 10時～20時
    for hour in range(10, 21):
      row = {}
      for day in days:
        row[day] = True
      calendar_[hour] = row
    start_time = make_aware(datetime.combine(start_day, time(hour=10, minute=0, second=0)))
    end_time = make_aware(datetime.combine(end_day, time(hour=20, minute=0, second=0)))
    booking_data = ExBooking.objects.filter(training__in=training_data).exclude(Q(start__gt=end_time) | Q(end__lt=start_time))
    for booking in booking_data:
      local_time = localtime(booking.start)
      booking_date = local_time.date()
      booking_hour = local_time.hour
      if (booking_hour in calendar_) and (booking_date in calendar_[booking_hour]):
        calendar_[booking_hour][booking_date] = False

    return render(request, 'app/ex_calendar.html', {
      'training_data': training_data,
      'calendar': calendar_,
      'days': days,
      'start_day': start_day,
      'end_day': end_day,
      'before': days[0] - timedelta(days=7),
      'next': days[-1] + timedelta(days=1),
      'today': today,
    })

class ExBookingView(TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = Training.objects.filter(id=self.kwargs['pk'])
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    hour = self.kwargs.get('hour')
    form = ExBookingForm(request.POST or None)
    objective = Master.objects.filter(category='目的')

    return render(request, 'app/ex_booking.html', {
      'training_data': training_data,
      'year': year,
      'month': month,
      'day': day,
      'hour': hour,
      'form': form,
      'objective': objective,
    })

  def post(self, request, *args, **kwargs):
    training_data = get_object_or_404(Training, id=self.kwargs['pk'])
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    hour = self.kwargs.get('hour')
    start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour))
    end_time = make_aware(datetime(year=year, month=month, day=day, hour=hour + 1))
    ExBooking_data = ExBooking.objects.filter(training=training_data, start=start_time)
    form = ExBookingForm(request.POST or None)
    if ExBooking_data.exists():
      return render(request, 'app/ex_booking_exists.html', {
        'training_data': training_data
      })
    else:
      if form.is_valid():
        Exbooking = ExBooking()
        Exbooking.training = training_data
        Exbooking.start = start_time
        Exbooking.end = end_time
        Exbooking.first_name = request.POST['first_name']
        Exbooking.last_name = request.POST['last_name']
        Exbooking.sex = request.POST['sex']
        Exbooking.age = request.POST['age']
        Exbooking.people = request.POST['people']
        Exbooking.email = request.POST['email']
        Exbooking.tel_number = request.POST['tel_number']
        Exbooking.objective = request.POST['objective']
        Exbooking.remarks = request.POST['remarks']
        Exbooking.save()
        return render(request, 'app/ex_thanks.html', {
          'training_data': training_data,
        })

    return render(request, 'app/ex_booking.html', {
      'training_data': training_data,
      'year': year,
      'month': month,
      'day': day,
      'hour': hour,
    })

class ExThanksView(TemplateView):
  def get(self, request, *args, **kwargs):
    training_data = request.booking.training

    return render(request, 'app/ex_thanks.html', {
      'training_data': training_data,
    })


class StaffMemberView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    form = MemberSearchForm(request.POST or None)

    return render(request, 'app/member.html', {
      'form': form,
    })

  def post(self, request, *args, **kwargs):
    #post_list = request.POST.getlist  # <input type="checkbox" name="delete"のnameに対応
    post_list_json = json.dumps(request.POST)
    request.session['post_list'] = post_list_json
    return redirect('member_list')

class StaffMemberListView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    serach_val = request.session.get('post_list')
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

    #for key,value in serach_val_json.items():
    #    print(value)

    return render(request, 'app/member_list.html', {
      'user_detail':user_detail,
    })

  def post(self, request, *args, **kwargs):
    post_pks = request.POST.getlist('select_user') # <input type="checkbox" name="select_user"のvalueを取得
    if post_pks :
      request.session['user_pk'] = post_pks #セッションにセット
      return redirect('member_input')
    else:
      serach_val = request.session.get('post_list')
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

      return render(request, 'app/member_list.html', {
        'user_detail':user_detail,
      })


class StaffMemberInputView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    user_pk = int(request.session.get('user_pk')[0]) #セッションからuserのid番号を引き継ぐ
    user_data = CustomUser.objects.get(id=user_pk)

    form = MemberForm(
      request.POST or None,
      initial={
        'member_no': user_data.member_no,
        'first_name':user_data.first_name,
        'last_name':user_data.last_name,
        'sex': user_data.sex,
        'birthday':user_data.birthday,
        'email':user_data.email,
        'tel_number':user_data.tel_number,
        'num_contracts':user_data.num_contracts,
        'stat_date':user_data.stat_date,
        'end_date':user_data.end_date,
        'is_shoes_custody':user_data.is_shoes_custody,
        'amount_money':user_data.amount_money,
        'memo':user_data.memo
      }
    )
    return render(request, 'app/member_input.html', {
      'form': form,
      'user_data': user_data
    })

  def post(self, request, *args, **kwargs):
    user_pk = request.POST.getlist('member_input') # <input type="checkbox" name="select_user"のvalueを取得
    form = MemberForm(request.POST or None)
    user_data = CustomUser.objects.get(id=user_pk[0])

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
      return redirect('member_input_ok')
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


class StaffMemberInputOkView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    form = MemberForm(request.POST or None)

    return render(request, 'app/member_input_ok.html', {
      'form': form,
    })

  def post(self, request, *args, **kwargs):
    return redirect('member')


class StaffNotificationView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    notification = Notification.objects.all()
    form = NotificationForm(
      request.POST or None,
      initial={
        'notice': notification.values('notice')[0]['notice']
      }
    )

    return render(request, 'app/notification.html', {
      'form': form,
    })

  def post(self, request, *args, **kwargs):
    form = NotificationForm(request.POST or None)
    if form.is_valid():
      notification = Notification.objects.get(id=1)
      notification.notice = form.cleaned_data['notice']
      notification.save()
      return redirect('notification_ok')

    return redirect('member')

class StaffNotificationOkView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):

    return render(request, 'app/notification_ok.html', {
    })

  def post(self, request, *args, **kwargs):
    return redirect('member')

class StaffHolidayView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):

    return render(request, 'app/notification_ok.html', {
    })

  def post(self, request, *args, **kwargs):
    return redirect('member')
