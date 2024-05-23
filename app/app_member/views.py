import calendar , json

from django.shortcuts import get_object_or_404, render ,redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.app_member.models import Booking, ExBooking
from app.app_staff.models import Staff, Notification
from app.app_staff.views import find_closing_exist_days__function, day_start_end_setting__function, \
  hour_minute_second__function, later_15minute__function
from accounts.models import Training ,CustomUser
from datetime import datetime, date, timedelta, time
from django.db.models import Q ,Count
from django.utils.timezone import localtime, make_aware
from app.app_member.forms import BookingForm, ExBookingForm
from app.app_staff.forms import NotificationForm


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
    training_data = Training.objects.filter(id=self.kwargs['training_id'])
    today = date.today()
    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    duplicates_num = training_data.values('duplicates_num')[0]['duplicates_num']  # 予約可能数取得
    training_id = self.kwargs['training_id']
    my_id = request.user.id # 自分

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
      for minute in [0, 15, 30, 45]:
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
    user_start_date = user_data.values('stat_date')[0]['stat_date']  # 契約開始
    user_end_date = user_data.values('end_date')[0]['end_date']  # 契約終了

    # just now
    now_time = make_aware(datetime.today())

    # 休館日取得
    close_date_start_time = make_aware(datetime.combine(start_day, time(hour=0, minute=0, second=0)))
    close_date_end_time = make_aware(datetime.combine(end_day, time(hour=23, minute=59, second=59)))
    close_date_data = find_closing_exist_days__function('C', close_date_start_time, close_date_end_time, None, None)
    black_date_data = find_closing_exist_days__function('B', close_date_start_time, close_date_end_time, training_id, None)

    for hour_calendar in calendar_:
      for minute_calendar in calendar_[hour_calendar]:
        for day_calendar in calendar_[hour_calendar][minute_calendar]:

          # 予約可能チェックポリシー（優先順）
          ## 時間 > CL都合（休館日、black.gray） > CS状態（予約可能期間、予約可能回数） > CS都合（今日予約したか？） > 他CS状況（他のお客の都合）

          # 時間を定義
          ## 作成日付をローカルタイムに変更
          day_calendar_j = day_start_end_setting__function(day_calendar.year, day_calendar.month, day_calendar.day)
          day_calendar_h_m_j = hour_minute_second__function(day_calendar, hour_calendar, minute_calendar, "00")

          # 時間チェック 現在から1時間後まで予約不可
          now_time_one = now_time + timedelta(hours=1)
          if day_calendar_h_m_j <= now_time_one:
              calendar_[hour_calendar][minute_calendar][day_calendar] = 20  # 時間切れ
              continue

          # 休館日チェック
          if close_date_data:
              re_val = close_check_front__function(close_date_data, day_calendar_j['today_j']) # 休館日チェック_フロント
              if re_val: # 休館日だった場合はスキップ
                 calendar_[hour_calendar][minute_calendar][day_calendar] = 21  # 休館日
                 continue

          # 黒灰ブロックチェック
          if black_date_data:
             re_val = black_check_front__function(black_date_data, day_calendar_h_m_j)
             if re_val == 'B': # 黒ブロックだった場合はスキップ
                calendar_[hour_calendar][minute_calendar][day_calendar] = 22  # 休館日
                continue
             elif re_val == 'G': # 廃ブロックだった場合はスキップ
                calendar_[hour_calendar][minute_calendar][day_calendar] = 23  # 休館日
                continue

          # 予約可能期間 自分の契約期間外「5:予約不可」
          if user_start_date <= day_calendar and day_calendar <= user_end_date:
             pass # なにもせず。予約可能回数判断へ移る
          else:
             calendar_[hour_calendar][minute_calendar][day_calendar] = 5  # 自分の契約期間外「予約不可」
             continue

          # 予約可能回数 自分の予約残数がない「6:予約不可」
          if user_num_times == 0:
             calendar_[hour_calendar][minute_calendar][day_calendar] = 6  # 自分の予約残数がない「6:予約不可」
             continue

          # 1日1海縛り 自分が「予約済み」
          if calendar_[hour_calendar][minute_calendar][day_calendar] == 1:  # 自分が「予約済み」
             continue

          # 予約チェック
          reserve_cd = reserve_check__function(day_calendar, minute_calendar, hour_calendar, booking_data, my_id, duplicates_num)
          calendar_[hour_calendar][minute_calendar][day_calendar] = reserve_cd

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
    user_num_times = user_detail.values('num_times')[0]['num_times']
    user_start_date = user_detail.values('stat_date')[0]['stat_date']  # 契約開始
    user_end_date = user_detail.values('end_date')[0]['end_date']  # 契約終了
    my_id = request.user.id # 自分
    training_id = self.kwargs['pk']

    year = self.kwargs.get('year')
    month = self.kwargs.get('month')
    day = self.kwargs.get('day')
    hour = self.kwargs.get('hour')
    minute = self.kwargs.get('minute')
    today = date.today()

    if year and month and day:
      # 週始め
      start_date = date(year=year, month=month, day=day)
    else:
      start_date = today

    # 45分後を瀬底する
    if minute == 0:
       hour_end = hour
       minute_end = 45
    elif minute == 15:
       hour_end = hour + 1
       minute_end = 0
    elif minute == 30:
       hour_end = hour + 1
       minute_end = 15
    else:
       hour_end = hour + 1
       minute_end = 30

    start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute))
    end_time = make_aware(datetime(year=year, month=month, day=day, hour=hour_end, minute=minute_end))

    duplicates_num = training_data_obj.values('duplicates_num')[0]['duplicates_num']  # 予約可能数取得
    booking_data = Booking.objects.filter(training=training_data, start=start_time)
    form = BookingForm(request.POST or None)

    # 休館日取得
    close_date_start_time = make_aware(datetime.combine(start_date, time(hour=0, minute=0, second=0)))
    close_date_end_time = make_aware(datetime.combine(start_date, time(hour=23, minute=59, second=59)))
    close_date_data = find_closing_exist_days__function('C', close_date_start_time, close_date_end_time, None, None)
    black_date_data = find_closing_exist_days__function('B', close_date_start_time, close_date_end_time, training_id, None)

    # just now
    now_time = make_aware(datetime.today())

    # 時間チェック 現在から1時間後まで予約不可
    now_time_one = now_time + timedelta(hours=1)
    if start_time <= now_time_one:
        err_msg = '予約時間が予約可能時間を過ぎています'
        return render(request, 'app/booking_exists.html', {
            'training_data': training_data,
            'err_msg': err_msg,
        })

    # 休館日チェック
    if close_date_data:
        re_val = close_check_front__function(close_date_data, start_time) # 休館日チェック_フロント
        if re_val: # 休館日だった場合はスキップ
            err_msg = '休館日です'
            return render(request, 'app/booking_exists.html', {
                'training_data': training_data,
                'err_msg':err_msg,
            })

    # 黒灰ブロックチェック
    if black_date_data:
        re_val = black_check_front__function(black_date_data, start_time)
        err_msg = ''
        if re_val == 'B': # 黒ブロックだった場合はスキップ
            err_msg = '他の予約と重なりました_B'
        elif re_val == 'G': # 廃ブロックだった場合はスキップ
            err_msg = '他の予約と重なりました_G'
        return render(request, 'app/booking_exists.html', {
            'training_data': training_data,
            'err_msg': err_msg,
        })

    # 予約可能期間 自分の契約期間外「5:予約不可」
    user_start_datetime = day_start_end_setting__function(user_start_date.year, user_start_date.month, user_start_date.day)['today_j']
    user_end_datetime = day_start_end_setting__function(user_end_date.year, user_end_date.month, user_end_date.day)['today_j']

    if user_start_datetime <= start_time and start_time <= user_end_datetime:
        pass  # なにもせず。予約可能回数判断へ移る
    else:
        err_msg = '契約期限が過ぎています_5'
        return render(request, 'app/booking_exists.html', {
            'training_data': training_data,
            'err_msg':err_msg,
        })

    # 予約可能回数 自分の予約残数がない「6:予約不可」
    if user_num_times == 0:
        err_msg = '予約残数がありません_6'
        return render(request, 'app/booking_exists.html', {
            'training_data': training_data,
            'err_msg': err_msg,
        })

    # ダブルブッキングチェック
    ## 予約チェック
    reserve_cd = reserve_check__function(start_date, minute, hour, booking_data, my_id, duplicates_num)
    if reserve_cd > 0:
        err_msg = '他の予約と重なった可能性があり、予約できませんでした。'
        return render(request, 'app/booking_exists.html', {
           'training_data': training_data,
            'err_msg': err_msg,
        })

    if form.is_valid():
        booking = Booking()
        booking.training = training_data
        booking.user = user_data
        booking.start = start_time
        booking.end = end_time
        booking.save()
        # 予約残数減数処理
        user_detail = CustomUser.objects.get(id=request.user.id)
        if user_num_times > 0 or user_num_times < 98:  # 0回または99回以上（サブスク）がセットされている場合は減数処理しない
           user_detail.num_times = user_num_times - 1
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


class MypageView(LoginRequiredMixin, TemplateView):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.filter(id=request.user.id)
    # 期間を算出
    user_start_date = user_data.values('stat_date')[0]['stat_date']  # 契約開始
    user_end_date = user_data.values('end_date')[0]['end_date']  # 契約終了
    user_date_dif = user_end_date.month - user_start_date.month

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

#################
# ---関数エリア---
#################
def close_check_front__function(close_date_data, day_calendar):
# 休館日チェック_フロント

  for close_date in close_date_data:
      if close_date.closing_type == 'C' and close_date.start == day_calendar:
        return True

  return False

def black_check_front__function(black_date_data, day_calendar):
  # 休館日チェック_フロント

  for close_date in black_date_data:
    if close_date.closing_type == 'B' and close_date.start + timedelta(hours=-1) <= day_calendar and close_date.end >= day_calendar + timedelta(minutes=15):
      return 'B'
    elif close_date.closing_type == 'G' and close_date.start <= day_calendar and close_date.end >= day_calendar + timedelta(minutes=15):
      return 'G'

  return False


def reserve_check__function(day_calendar, minute_calendar, hour_calendar, booking_data, my_id, duplicates_num):
    # 予約チェック
    ## 基本的な考え方：45分後の予約時間まで15分刻みで掘り下げて、その１時間帯で予約が埋まっていたら「満席」：他人の場合 or 「予約不可」：自分が予約あった場合

    reserve_cd = 0 # 返り値の宣言

    arr_other_booking_cnt = {}
    arr_other_booking_cnt[0] = 0 #0-15分枠
    arr_other_booking_cnt[1] = 0 #15-30分枠
    arr_other_booking_cnt[2] = 0 #30-45分枠
    arr_other_booking_cnt[3] = 0 #45-60分枠

    # 初期設定
    minute_calendar_after = minute_calendar
    hour_calendar_after = hour_calendar

    for i, other_booking in enumerate(arr_other_booking_cnt):  # 0-3 4回す

        if i == 0:
            # 1ループ目
            pass
        else:
            # 15分後をセットする。軸を45分後まで15分刻みで掘り下げて予約を確認する
            after = later_15minute__function(minute_calendar_after, hour_calendar_after)
            hour_calendar_after = after['hour_end']
            minute_calendar_after = after['minute_end']

        datetime_calendar_after = hour_minute_second__function(day_calendar, hour_calendar_after, minute_calendar_after, "00")

        minute_calendar_before = minute_calendar_after
        hour_calendar_before = hour_calendar_after

        # 45分前をセットする。今いる時間軸より、45分前の時間にいくつ予約が入っているかを数えるため
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

        datetime_calendar_before = hour_minute_second__function(day_calendar, hour_calendar_before, minute_calendar_before, "00")

        # 予約を確認する
        for booking in booking_data:
            booking_local_datetime = localtime(booking.start)
            booking_date = booking_local_datetime.date()

            if datetime_calendar_before <= booking_local_datetime and booking_local_datetime <= datetime_calendar_after: # 45分遡って、予約があった場合数える
                if booking.user.id == my_id:  # 自分の予約？
                    if i == 0:
                        reserve_cd = 1  # 自分が「予約」
                else:
                    arr_other_booking_cnt[other_booking] = arr_other_booking_cnt[other_booking] + 1

            if day_calendar == booking_date:
                if reserve_cd != 1:
                    reserve_cd = 7  # 自分が今日「予約済み」のため、他の時間の予約ができない

    # 自分が予約済みのとき、他人の都合判断はしない
    if reserve_cd == 7:
       return reserve_cd

    # 他人の都合判断
    if reserve_cd != 1:
        if arr_other_booking_cnt[0] >= duplicates_num or arr_other_booking_cnt[1] >= duplicates_num or arr_other_booking_cnt[2] >= duplicates_num or arr_other_booking_cnt[3] >= duplicates_num:
            reserve_cd = 2  # 「満席」
        elif duplicates_num > 1 and (arr_other_booking_cnt[0] > 0 or arr_other_booking_cnt[1] > 0 or arr_other_booking_cnt[2] > 0 or arr_other_booking_cnt[3] > 0):
            reserve_cd = 4  # 「4:残りわずか」(「予約１件以上」かつ「空き１件以上)

    return reserve_cd
