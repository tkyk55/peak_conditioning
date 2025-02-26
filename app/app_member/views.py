import calendar, json, random, string

from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.app_member.models import Booking, ExBooking, Master
from app.app_staff.models import Staff, Notification
from app.app_staff.views import find_closing_exist_days__function, day_start_end_setting__function
from accounts.models import Training, CustomUser
from datetime import datetime, date, timedelta, time
from django.db.models import Q, Count
from django.utils.timezone import localtime, make_aware
from django.utils import timezone
from app.app_member.forms import BookingForm, ExBookingForm, ExEmailForm
from config.utils import send_custom_email, send_email__function, find_closing_exist_days__function, day_start_end_setting__function
# from icecream import ic
import ast
from dateutil.relativedelta import relativedelta


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
        my_id = request.user.id  # 自分

        if year and month and day:
            # 週始め
            start_date = date(year=year, month=month, day=day)
        else:
            start_date = today
        # 1週間
        days = [start_date + timedelta(days=day) for day in range(7)]
        start_day = days[0]
        end_day = days[-1]

        # メンバーカレンダー作成
        calendar = member_calemdar__function(days)

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

        for hour_calendar in calendar:
            for minute_calendar in calendar[hour_calendar]:
                for day_calendar in calendar[hour_calendar][minute_calendar]:

                    # 予約可能チェックポリシー（優先順）
                    ## 時間 > CL都合（休館日、black.gray） > CS状態（予約可能期間、予約可能回数） > CS都合（今日予約したか？） > 他CS状況（他のお客の都合）

                    # 時間を定義
                    ## 作成日付をローカルタイムに変更
                    day_calendar_j = day_start_end_setting__function(day_calendar.year, day_calendar.month, day_calendar.day)
                    day_calendar_h_m_j = make_aware(datetime(year=day_calendar.year, month=day_calendar.month, day=day_calendar.day, hour=int(hour_calendar), minute=int(minute_calendar)))

                    # 時間チェック 現在から1時間後まで予約不可
                    now_time_one = now_time + timedelta(hours=1)
                    if day_calendar_h_m_j <= now_time_one:
                        calendar[hour_calendar][minute_calendar][day_calendar] = 20  # 時間切れ
                        continue

                    # 休館日チェック
                    if close_date_data:
                        re_val = close_check_front__function(close_date_data, day_calendar_j['today_j'])  # 休館日チェック_フロント
                        if re_val:  # 休館日だった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 21  # 休館日
                            continue

                    # 黒灰ブロックチェック
                    if black_date_data:
                        re_val = black_check_front__function(black_date_data, day_calendar_h_m_j)
                        if re_val == 'B':  # 黒ブロックだった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 22  # 休館日
                            continue
                        elif re_val == 'G':  # 廃ブロックだった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 23  # 休館日
                            continue

                    # 予約可能期間 自分の契約期間外「5:予約不可」
                    if user_start_date <= day_calendar and day_calendar <= user_end_date:
                        pass  # なにもせず。予約可能回数判断へ移る
                    else:
                        calendar[hour_calendar][minute_calendar][day_calendar] = 5  # 自分の契約期間外「予約不可」
                        continue

                    # 予約可能回数 自分の予約残数がない「6:予約不可」
                    if user_num_times == 0:
                        calendar[hour_calendar][minute_calendar][day_calendar] = 6  # 自分の予約残数がない「6:予約不可」
                        continue

                    # 1日1海縛り 自分が「予約済み」
                    if calendar[hour_calendar][minute_calendar][day_calendar] == 1:  # 自分が「予約済み」
                        continue

                    # 予約チェック
                    reserve_cd = reserve_check__function(day_calendar, minute_calendar, hour_calendar, booking_data, my_id, duplicates_num)
                    calendar[hour_calendar][minute_calendar][day_calendar] = reserve_cd

        return render(request, 'app/calendar.html', {
            'training_data': training_data,
            'calendar': calendar,
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
        my_id = request.user.id  # 自分
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

        start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute))
        end_time = make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute)) + timedelta(minutes=45) # 45分後を設定

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
            re_val = close_check_front__function(close_date_data, start_time)  # 休館日チェック_フロント
            if re_val:  # 休館日だった場合はスキップ
                err_msg = '休館日です'
                return render(request, 'app/booking_exists.html', {
                    'training_data': training_data,
                    'err_msg': err_msg,
                })

        # 黒灰ブロックチェック
        if black_date_data:
            re_val = black_check_front__function(black_date_data, start_time)
            err_msg = ''
            if re_val == 'B':  # 黒ブロックだった場合はスキップ
                err_msg = '他の予約と重なりました_B'
            elif re_val == 'G':  # 廃ブロックだった場合はスキップ
                err_msg = '他の予約と重なりました_G'
            return render(request, 'app/booking_exists.html', {
                'training_data': training_data,
                'err_msg': err_msg,
            })

        # 予約可能期間 自分の契約期間外「5:予約不可」
        user_start_datetime = \
        day_start_end_setting__function(user_start_date.year, user_start_date.month, user_start_date.day)['today_j']
        user_end_datetime = day_start_end_setting__function(user_end_date.year, user_end_date.month, user_end_date.day)['today_j']

        if user_start_datetime <= start_time and start_time <= user_end_datetime:
            pass  # なにもせず。予約可能回数判断へ移る
        else:
            err_msg = '契約期限が過ぎています_5'
            return render(request, 'app/booking_exists.html', {
                'training_data': training_data,
                'err_msg': err_msg,
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

            # email_send
            master_data = Master.objects.get(id=1)
            site_url = master_data.site_url
            end_datetime = start_time + timedelta(hours=1)
            context = {
                'user_name': user_data.first_name + ' ' + user_data.last_name,
                'start_datetime': start_time.strftime('%Y-%m-%d %H:%M'),
                'end_datetime': end_datetime.strftime('%Y-%m-%d %H:%M'),
                'site_url': site_url,
                'training_name': training_data.name
            }
            email_templates_id = 1  # 【peak_conditions】ご予約ありがとうございます
            send_email__function(user_data.email, context, email_templates_id)

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
        start_time = timezone.now()
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
    # 予約キャンセル
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)

        # 過去の予約は出さないようにするため、現時間より前の予約は除外する
        start_time = datetime.today()
        booking_data = Booking.objects.filter(user=request.user.id).exclude(Q(end__lt=start_time))

        training_category = booking_data.values('training').annotate(training_cnt=Count('training')).order_by(
            'training')

        return render(request, 'app/cancel.html', {
            'user_data': user_data,
            'booking_data': booking_data,
            'training_category': training_category
        })

    def post(self, request):
        post_pks = request.POST.getlist('delete')  # <input type="checkbox" name="delete"のnameに対応

        # 予約情報をメール送信内容編集のためDBから取得しておく
        booking_data = Booking.objects.filter(pk__in=post_pks)
        booking_text = ''
        for booking in booking_data:
            start = localtime(booking.start)
            start_time = start.strftime('%Y/%m/%d %H:%M')
            end = start + timedelta(hours=1)
            end_time = end.strftime('%Y/%m/%d %H:%M')
            booking_text += f"トレーニング名：{booking.training.name}\n"
            booking_text += f"開始時間：{start_time}\n"
            booking_text += f"終了時間：{end_time}\n\n"  # トレーニング間の改行

        Booking.objects.filter(pk__in=post_pks).delete()

        user_data = CustomUser.objects.get(id=request.user.id)
        num_times = user_data.num_times
        user_detail = CustomUser.objects.get(id=request.user.id)
        if num_times < 98:  # 99回以上（サブスク考慮）がセットされている場合は加算処理しない
            user_detail.num_times = num_times + len(post_pks)
            user_detail.save()

        # email_send
        master_data = Master.objects.get(id=1)
        site_url = master_data.site_url
        context = {
            'user_name': user_data.first_name + ' ' + user_data.last_name,
            'booking_text': booking_text,
            'site_url': site_url
        }
        email_templates_id = 2
        send_email__function(user_data.email, context, email_templates_id)

        user_data = CustomUser.objects.get(id=request.user.id)
        booking_data = Booking.objects.filter(user=request.user.id)
        training_category = booking_data.values('training').annotate(training_cnt=Count('training')).order_by('training')

        return render(request, 'app/cancelok.html', {
            'user_data': user_data,
            'booking_data': booking_data,
            'training_category': training_category
        })


class ExEmailView(TemplateView):
    def get(self, request, *args, **kwargs):
        form = ExEmailForm(request.POST or None)

        return render(request, 'app/ex_email.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        email = request.POST.getlist('email')  # <input type="submit" name="email"のnameに対応

        # ex_bookingにメアドがあるかチェック
        ex_booking_data = ExBooking.objects.filter(email=email[0], is_valid=1).order_by('-updated_at')

        # emailがない：status=0で登録
        if not ex_booking_data:
            ex_status0_input__function(email[0])
            return render(request, 'app/ex_email_send_ok.html', {
                'email': email[0]
            })

        if 'delete' in request.POST:
            ex_booking_del_data = ExBooking.objects.get(id=ex_booking_data[0].id)
            ex_booking_del_data.version += 1
            ex_booking_del_data.is_valid = 0
            ex_booking_del_data.save()
            return redirect('ex_delete')

        if 'resend' in request.POST:
            ex_booking_del_data = ExBooking.objects.get(id=ex_booking_data[0].id)
            ex_booking_del_data.version += 1
            ex_booking_del_data.is_valid = 0
            ex_booking_del_data.save()
            return redirect('ex_email')

        # 有効期限のセット
        expiration_date = localtime(ex_booking_data[0].expiration_date)

        # emailがある,status=0、有効期限内：メール認証されていません画面
        if ex_booking_data[0].status == '0' and expiration_date >= make_aware(datetime.today()):
            return render(request, 'app/ex_certification_not.html', {
                'email': email[0]
            })

        # emailがある,status=0、有効期限外：メール認証の有効期限が終了しました画面遷移
        if ex_booking_data[0].status == '0' and expiration_date < make_aware(datetime.today()):
            return render(request, 'app/ex_expiration_date_invalid.html', {
                'email': email[0]
            })

        # emailがある,status=1,有効期限内：予約選択画面
        if ex_booking_data[0].status == '1' and expiration_date >= make_aware(datetime.today()):
            request.session['ex_booking_data_id'] = ex_booking_data[0].id  # セッションを設定しておく
            return redirect('ex_reserve')

        # emailがある,status=1,有効期限外：このメールアドレスは有効期限が終了しました画面遷移
        if ex_booking_data[0].status == '1' and expiration_date < make_aware(datetime.today()):
            return render(request, 'app/ex_email_invalid.html', {
                'email': email[0]
            })

        # emailがある,status=2,有効期限内：予約確認画面
        if ex_booking_data[0].status == '2' and expiration_date >= make_aware(datetime.today()):
            request.session['ex_booking_data_id'] = ex_booking_data[0].id  # セッションを設定しておく
            form = ExBookingForm(
                initial={
                    'first_name': ex_booking_data[0].first_name,
                    'last_name': ex_booking_data[0].last_name,
                    'sex': str(ex_booking_data[0].sex),
                    'age': str(ex_booking_data[0].age),
                    'people': str(ex_booking_data[0].people),
                    'email': ex_booking_data[0].email,
                    'email_ch': ex_booking_data[0].email,
                    'tel_number': ex_booking_data[0].tel_number,
                    'objective': ex_booking_data[0].objective,
                    'remarks': ex_booking_data[0].remarks
                }
            )

            return render(request, 'app/ex_booking_conf.html', {
                'training_data': ex_booking_data[0].training,
                'start': ex_booking_data[0].start,
                'end': ex_booking_data[0].end,
                'form': form,  # 入力値を保持したままフォームを再表示
                'status': ex_booking_data[0].status,
            })
            # else:
            #     # フォームが無効な場合の処理
            #     for field, errors in form.errors.items():
            #     #   # 各項目のエラーメッセージを取得
            #        for error in errors:
            #           print(f"{field}: {error}")

        # emailがある,status=2、有効期限外：このメールアドレスは有効期限が終了しました画面遷移
        if ex_booking_data[0].status == '2' and expiration_date < make_aware(datetime.today()):
            return render(request, 'app/ex_email_invalid.html', {
            })

        return render(request, 'app/ex_email_invalid.html', {
        })


class ExCertificationView(TemplateView):
    def get(self, request, *args, **kwargs):
        url_param = request.GET.get('p')  # urlパラメータ取得

        # urlパラメータがなかった場合。このURLは無効です画面遷移
        if not url_param:
            return render(request, 'app/ex_certification_invalid.html', {
            })

        # 認証urlの確認
        ex_booking_data_filter = ExBooking.objects.filter(url_param=url_param, is_valid=1)
        if not ex_booking_data_filter:
            return render(request, 'app/ex_certification_invalid.html', {
            })

        ex_booking_data = ExBooking.objects.get(id=ex_booking_data_filter.values('id')[0]['id'])

        # 有効期限セット
        expiration_date = localtime(ex_booking_data.expiration_date)

        # status=0、かつ有効期限内の場合、status=1 に変更してexcalenderへ
        if ex_booking_data.status == '0' and expiration_date >= make_aware(datetime.today()):
            ex_booking_data.expiration_date = expiration_date + timedelta(days=1)  # 有効期限を1日伸ばす
            ex_booking_data.status = '1'  # 認証済み
            ex_booking_data.version += 1
            ex_booking_data.save()
            request.session['ex_booking_data_id'] = ex_booking_data.id  # セッションを設定しておく
            return redirect('ex_reserve')
        else:
            return render(request, 'app/ex_certification_invalid.html', {
            })

    def post(self, request, *args, **kwargs):
        email = request.POST.getlist('email')  # <input type="submit" name="email"のnameに対応
        # ex_bookingにメアドがあるかチェック
        ex_booking_data = ExBooking.objects.filter(email=email[0], is_valid=1).order_by('-updated_at')

        if ex_booking_data and 'resend' in request.POST:
            ex_booking_del_data = ExBooking.objects.get(id=ex_booking_data[0].id)
            ex_booking_del_data.version += 1
            ex_booking_del_data.is_valid = 0
            ex_booking_del_data.save()

        return redirect('ex_email')


class ExeEpirationDateInvalidView(TemplateView):
    def get(self, request, *args, **kwargs):
        ex_id = self.kwargs.get('ex_id')

        return render(request, 'app/ex_expiration_date_invalid.html', {
        })


class ExReserveView(TemplateView):
    def get(self, request, *args, **kwargs):
        ex_booking_data_id = request.session.get('ex_booking_data_id')

        # セッションがない場合は無効
        if not ex_booking_data_id:
            return render(request, 'app/ex_certification_not.html')

        Training_data = Training.objects.filter(experience_flg=1)

        return render(request, 'app/ex_reserve.html', {
            'training_data': Training_data,
        })


class ExCalendarView(TemplateView):
    def get(self, request, *args, **kwargs):
        ex_booking_data_id = request.session.get('ex_booking_data_id')
        # セッションがなければ無効
        if not ex_booking_data_id:
            return render(request, 'app/ex_expiration_date_not.html')

        # 有効期限を確認する
        ex_booking_data = ExBooking.objects.filter(id=ex_booking_data_id).first()
        if not ex_booking_data:
            return render(request, 'app/ex_email_invalid.html')
        expiration_date = localtime(ex_booking_data.expiration_date)
        if expiration_date < make_aware(datetime.today()):  # 有効期限が過ぎていたら終了
            return render(request, 'app/ex_expiration_date_invalid.html', {
                'email': ex_booking_data.email
            })

        # status=2の場合、予約確認画面へ
        if ex_booking_data.status == '2' and expiration_date >= make_aware(datetime.today()):
            return redirect('ex_reserve')  # todo

        # emailがある,status=2、有効期限外：このメールアドレスは有効期限が終了しました画面遷移
        if ex_booking_data.status == '2' and expiration_date < make_aware(datetime.today()):
            return render(request, 'app/ex_email_invalid.html', {
            })

        training_data = Training.objects.filter(id=self.kwargs['training_id'])
        today = date.today()
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        training_id = self.kwargs['training_id']

        if year and month and day:
            # 週始め
            start_date = date(year=year, month=month, day=day)
        else:
            start_date = today
        # 1週間
        days = [start_date + timedelta(days=day) for day in range(7)]
        start_day = days[0]
        end_day = days[-1]

        # 今日以下判定
        today_flg = '0'
        if start_date <= today:
            today_flg = '1'

        # 1ヶ月先判定
        one_month_later = today + relativedelta(months=1)
        one_month_flg = '0'
        if end_day >= one_month_later:
            one_month_flg = '1'

        # メンバーカレンダー作成
        calendar = member_calemdar__function(days)

        start_time = make_aware(datetime.combine(start_day, time(hour=10, minute=0, second=0)))
        end_time = make_aware(datetime.combine(end_day, time(hour=20, minute=0, second=0)))
        booking_data = ExBooking.objects.filter(training__in=training_data, is_valid=1).exclude(
            Q(start__gt=end_time) | Q(end__lt=start_time))

        # just now
        now_time = make_aware(datetime.today())

        # 休館日取得
        close_date_start_time = make_aware(datetime.combine(start_day, time(hour=0, minute=0, second=0)))
        close_date_end_time = make_aware(datetime.combine(end_day, time(hour=23, minute=59, second=59)))
        close_date_data = find_closing_exist_days__function('C', close_date_start_time, close_date_end_time, None, None)
        black_date_data = find_closing_exist_days__function('B', close_date_start_time, close_date_end_time,
                                                            training_id, None)

        for hour_calendar in calendar:
            for minute_calendar in calendar[hour_calendar]:
                for day_calendar in calendar[hour_calendar][minute_calendar]:

                    # 予約可能チェックポリシー（優先順）
                    ## 時間 > CL都合（休館日、black.gray） > CS状態（予約可能期間、予約可能回数） > CS都合（今日予約したか？） > 他CS状況（他のお客の都合）

                    # 時間を定義
                    ## 作成日付をローカルタイムに変更
                    day_calendar_j = day_start_end_setting__function(day_calendar.year, day_calendar.month, day_calendar.day)
                    day_calendar_h_m_j = make_aware(datetime(year=day_calendar.year, month=day_calendar.month, day=day_calendar.day, hour=int(hour_calendar), minute=int(minute_calendar)))

                    # 時間チェック 現在から1時間後まで予約不可
                    now_time_one = now_time + timedelta(hours=1)
                    if day_calendar_h_m_j <= now_time_one:
                        calendar[hour_calendar][minute_calendar][day_calendar] = 20  # 時間切れ
                        continue

                    # 休館日チェック
                    if close_date_data:
                        re_val = close_check_front__function(close_date_data, day_calendar_j['today_j'])  # 休館日チェック_フロント
                        if re_val:  # 休館日だった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 21  # 休館日
                            continue

                    # 黒灰ブロックチェック
                    if black_date_data:
                        re_val = black_check_front__function(black_date_data, day_calendar_h_m_j)
                        if re_val == 'B':  # 黒ブロックだった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 22  # 休館日
                            continue
                        elif re_val == 'G':  # 廃ブロックだった場合はスキップ
                            calendar[hour_calendar][minute_calendar][day_calendar] = 23  # 休館日
                            continue

                    # 1日1海縛り 自分が「予約済み」
                    if calendar[hour_calendar][minute_calendar][day_calendar] == 1:  # 自分が「予約済み」
                        continue

                    # 予約チェック
                    reserve_cd = reserve_check__function(day_calendar, minute_calendar, hour_calendar, booking_data,
                                                         ex_booking_data_id, 1)
                    calendar[hour_calendar][minute_calendar][day_calendar] = reserve_cd

        return render(request, 'app/ex_calendar.html', {
            'training_data': training_data,
            'calendar': calendar,
            'days': days,
            'start_day': start_day,
            'end_day': end_day,
            'before': days[0] - timedelta(days=7),
            'next': days[-1] + timedelta(days=1),
            'today': today,
            'today_flg': today_flg,
            'one_month_flg': one_month_flg,
        })

    def post(self, request, *args, **kwargs):
        email = request.POST.getlist('email')  # <input type="submit" name="email"のnameに対応
        form = ExEmailForm(request.POST or None)

        # ex_bookingにメアドがあるかチェック
        ex_booking_data = ExBooking.objects.filter(email=email[0], is_valid=1).order_by('-updated_at')

        if ex_booking_data and 'resend' in request.POST:
            ex_booking_del_data = ExBooking.objects.get(id=ex_booking_data[0].id)
            ex_booking_del_data.version += 1
            ex_booking_del_data.is_valid = 0
            ex_booking_del_data.save()
            return redirect('ex_email')
        else:
            return redirect('ex_email')

class ExBookingView(TemplateView):
    def get(self, request, *args, **kwargs):
        ex_booking_data_id = request.session.get('ex_booking_data_id')
        # セッションがなければ無効
        if not ex_booking_data_id:
            return render(request, 'app/ex_expiration_date_invalid.html')

        # 有効期限を確認する
        ex_booking_data = ExBooking.objects.get(id=ex_booking_data_id)
        if not ex_booking_data:
            return render(request, 'app/ex_expiration_date_invalid.html')
        expiration_date = localtime(ex_booking_data.expiration_date)
        if expiration_date < make_aware(datetime.today()):  # 有効期限が過ぎていたら終了
            return render(request, 'app/ex_expiration_date_invalid.html')

        training_data = Training.objects.get(id=self.kwargs['pk'])
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')
        if year and month and day:
            # 週始め
            start_date = date(year=year, month=month, day=day)
        else:
            start_date = date.today()
        start = make_aware(datetime.combine(start_date, time(hour=hour, minute=minute, second=0)))
        end = start + timedelta(hours=1)

        form = ExBookingForm(request.POST or None,
                             initial={
                                 'email': ex_booking_data.email,
                             }
                             )

        return render(request, 'app/ex_booking.html', {
            'training_data': training_data,
            'start': start,
            'end': end,
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        ex_booking_data_id = request.session.get('ex_booking_data_id')
        ex_booking_data = get_object_or_404(ExBooking, id=ex_booking_data_id)

        if not ex_booking_data:
            return render(request, 'app/ex_expiration_date_invalid.html')

        expiration_date = localtime(ex_booking_data.expiration_date)
        if expiration_date < make_aware(datetime.today()):
            return render(request, 'app/ex_expiration_date_invalid.html')

        training_data = get_object_or_404(Training, id=self.kwargs['pk'])
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        minute = self.kwargs.get('minute')
        start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute))
        end_time = start_time + timedelta(hours=1)

        other_ExBooking_data = ExBooking.objects.filter(training=training_data, start=start_time, is_valid=1).exclude(
            id=ex_booking_data_id)
        form = ExBookingForm(request.POST)

        if other_ExBooking_data.exists():
            return render(request, 'app/ex_booking_exists.html', {
                'training_data': training_data
            })

        if 'confirm' in request.POST:
            if form.is_valid():
                # 確認画面へ
                return render(request, 'app/ex_booking_conf.html', {
                    'training_data': training_data,
                    'start': start_time,
                    'end': end_time,
                    'form': form,
                })

        elif 'back' in request.POST:
            form = ExBookingForm(request.POST or None,
                                 initial={
                                     'first_name': request.POST.getlist('first_name'),
                                     'last_name': request.POST.getlist('last_name'),
                                     'sex': request.POST.getlist('sex'),
                                     'age': request.POST.getlist('age'),
                                     'people': request.POST.getlist('people'),
                                     'email': request.POST.getlist('email'),
                                     'tel_number': request.POST.getlist('tel_number'),
                                     'objective': request.POST.getlist('objective'),
                                     'remarks': request.POST.getlist('remarks'),
                                 }
                                 )

            str_list = request.POST.getlist('objective')[0]  # チェエクした目的を取得
            actual_list = ast.literal_eval(str_list)

            # 入力画面に戻る
            return render(request, 'app/ex_booking.html', {
                'training_data': training_data,
                'start': start_time,
                'end': end_time,
                'form': form,  # 入力値を保持したままフォームを再表示
                'objective': actual_list,  # チェックした目的を再表示するため
            })

        elif 'submit' in request.POST:
            # データベースに保存
            ex_booking_data.training = training_data
            ex_booking_data.start = start_time
            ex_booking_data.end = end_time
            ex_booking_data.first_name = request.POST.getlist('first_name')[0]
            ex_booking_data.last_name = request.POST.getlist('last_name')[0]
            ex_booking_data.sex = request.POST.getlist('sex')[0]
            ex_booking_data.age = request.POST.getlist('age')[0]
            ex_booking_data.people = request.POST.getlist('people')[0]
            ex_booking_data.email = request.POST.getlist('email')[0]
            ex_booking_data.tel_number = request.POST.getlist('tel_number')[0]
            ex_booking_data.objective = ",".join(request.POST.getlist('objective'))
            ex_booking_data.remarks = request.POST.getlist('remarks')[0]
            ex_booking_data.status = '2'
            ex_booking_data.expiration_date = start_time
            ex_booking_data.version += 1
            ex_booking_data.save()

            # mail
            return redirect('ex_thanks')

        return render(request, 'app/ex_booking.html', {
            'training_data': training_data,
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'form': form,
        })


class ExThanksView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'app/ex_thanks.html', {
        })


class ExDeleteView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'app/ex_delete.html', {
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
        if close_date.closing_type == 'B' and close_date.start + timedelta(minutes=-45) <= day_calendar and close_date.end >= day_calendar + timedelta(minutes=15):
            return 'B'
        elif close_date.closing_type == 'G' and close_date.start <= day_calendar and close_date.end >= day_calendar + timedelta(minutes=15):
            return 'G'

    return False


def reserve_check__function(day_calendar, minute_calendar, hour_calendar, booking_data, my_id, duplicates_num):
    # 予約チェック
    ## 基本的な考え方：45分前後の予約時間を検索し、その時間枠で予約が埋まっていたら「満席」：他人の場合 or 「予約不可」：自分が予約あった場合

    reserve_cd = 0  # 返り値の宣言

    # 初期設定
    arr_other_booking_cnt = {}

    for i in range(duplicates_num):
        arr_other_booking_cnt[i] = 0

    for i in range(duplicates_num):

        # 遡りstart時間セット
        datetime_calendar = make_aware(datetime(year=day_calendar.year, month=day_calendar.month, day=day_calendar.day, hour=int(hour_calendar), minute=int(minute_calendar)))
        ## 遡り45分前をセットする
        datetime_calendar_before = make_aware(datetime(year=day_calendar.year, month=day_calendar.month, day=day_calendar.day, hour=int(hour_calendar), minute=int(minute_calendar))) - timedelta(minutes=45)

        # 遡りend時間セット
        ## 45分後をセットする
        datetime_calendar_after = make_aware(datetime(year=day_calendar.year, month=day_calendar.month, day=day_calendar.day, hour=int(hour_calendar), minute=int(minute_calendar))) + timedelta(minutes=45)

        # 予約を確認する
        for booking in booking_data:
            booking_local_datetime = localtime(booking.start)
            booking_date = booking_local_datetime.date()
            booking_date_before = booking_local_datetime - timedelta(minutes=45)
            booking_date_after = booking_local_datetime + timedelta(minutes=45)

            if hasattr(booking, 'training_no'):  # 'training_no' 属性が存在するかチェック
                if booking_date_before <= datetime_calendar and datetime_calendar < booking_local_datetime \
                        and booking.training_no == i:  # 45分前後に予約時間とtraning_noが重複_Noと一致した場合
                    if booking.user.id == my_id:  # 自分の予約？
                        reserve_cd = 7  # 自分が今日「予約済み」のため、他の時間の予約ができない
                    else:
                        arr_other_booking_cnt[i] = arr_other_booking_cnt[i] + 1
                if booking_local_datetime <= datetime_calendar and datetime_calendar <= booking_date_after \
                        and booking.training_no == i:  # 45分前後に予約時間とtraning_noが重複_Noと一致した場合
                    if booking.user.id == my_id:  # 自分の予約？
                        reserve_cd = 1  # 自分が「予約」
                    else:
                        arr_other_booking_cnt[i] = arr_other_booking_cnt[i] + 1

                if day_calendar == booking_date:
                    if reserve_cd != 1 and booking.user.id == my_id:
                        reserve_cd = 7  # 自分が今日「予約済み」のため、他の時間の予約ができない
            else:  # exbookinの場合
                if datetime_calendar_before <= booking_local_datetime and booking_local_datetime <= datetime_calendar_after:
                    # ExBooking で user が存在しない場合の処理
                    if booking.id == my_id:  # 自分の予約？
                        reserve_cd = 1  # 自分が「予約」
                    else:
                        arr_other_booking_cnt[i] = 1
                        continue

    # 自分が予約済みのとき、他人の都合判断はしない
    if reserve_cd == 7:
        return reserve_cd

    # 他人の都合判断
    if reserve_cd != 1:
        other_booking_cnt_all = 0  # 全枠の予約埋まり数
        for i in range(duplicates_num):
            other_booking_cnt_all = other_booking_cnt_all + arr_other_booking_cnt[i]

        if other_booking_cnt_all >= duplicates_num:
            reserve_cd = 2  # 「満席」
        elif duplicates_num > 1 and other_booking_cnt_all > 0 and duplicates_num - other_booking_cnt_all <= 1:
            reserve_cd = 4  # 「4:残りわずか」(「予約１件以上」かつ 空き2件以下)

    return reserve_cd


def ex_status0_input__function(email):
    ex_booking_data = ExBooking()
    ex_booking_data.status = 0
    ex_booking_data.email = email
    ex_booking_data.expiration_date = make_aware(datetime.today()) + timedelta(hours=1)  # 有効期限は今から1時間
    ex_booking_data.version = 1
    ex_booking_data.save()
    # response_text = f"url_param: {ex_booking_data.url_param}, Email: {ex_booking_data.email}, ID: {ex_booking_data.id}"

    # email_send
    master_data = Master.objects.get(id=1)
    site_url = master_data.site_url
    certification_url = site_url + '/ex_reserve/certification?p=' + ex_booking_data.url_param
    context = {
        'certification_url': certification_url,
        'site_url': site_url
    }
    email_templates_id = 4
    send_email__function(email, context, email_templates_id)
    return


def member_calemdar__function(days):
    calendar = {}
    # 9時～19時
    for hour in range(9, 20):
        mrow = {}
        for minute in ['00', '15', '30', '45']:
            # 19時台の場合、19:00以外をスキップ
            if hour == 19 and minute != '00':
                continue
            row = {}
            for day in days:
                row[day] = 0  # 予約可
            mrow[minute] = row
        calendar[hour] = mrow

    return calendar
