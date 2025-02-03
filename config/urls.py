"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from accounts import views
from django.conf.urls.static import static
from django.conf import settings
from app.app_member import views as app_member_views
from app.app_staff import views as app_staff_views
import debug_toolbar

app_name = 'accounts'
urlpatterns = [
    path('admin/', admin.site.urls),
    #path('',TemplateView.as_view(template_name='home.html'), name='home'),
    path('',include('app.app_member.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LoginView.as_view(), name='logout'),
    path('accounts/nippo/', views.NippoView.as_view(), name='nippo-list'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('reserve/', views.ReserveView.as_view(), name='reserve'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('staff/', app_staff_views.StaffView.as_view(), name='staff'),
    path('staff/calendar/<int:year>/<int:month>/<int:day>/', app_staff_views.StaffCalendarView.as_view(), name='staff_calendar'),
    path('staff/member/', app_staff_views.StaffMemberView.as_view(), name='member'),
    path('staff/member/list', app_staff_views.StaffMemberListView.as_view(), name='member_list'),
    path('staff/member/list/<int:training_id>/<int:training_no>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>', app_staff_views.StaffMemberListView.as_view(), name='member_list'),
    path('staff/member/input', app_staff_views.StaffMemberInputView.as_view(), name='member_input'),
    path('staff/notification', app_staff_views.StaffNotificationView.as_view(), name='notification'),
    path('staff/menu', app_staff_views.StaffMenuView.as_view(), name='staff_menu'),
    path('staff/input', app_staff_views.StaffInputView.as_view(), name='staff_input'),
    path('staff/list', app_staff_views.StaffListView.as_view(), name='staff_list'),
    path('staff/work/input/<int:id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffWorkInputView.as_view(), name='staff_work_input'),
    path('staff/booking/input/<int:training_id>/<int:training_no>/<int:booking_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffBookingInputView.as_view(), name='staff_booking_input'),
    path('staff/booking/input/<int:training_id>/<int:training_no>/<int:booking_id>/<int:err_cd>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffBookingInputView.as_view(), name='staff_booking_input'),
    path('staff/booking/input/<int:training_id>/<int:training_no>/<int:booking_id>/<int:user_id>/<int:err_cd>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffBookingInputView.as_view(), name='staff_booking_input'),
    path('staff/booking/input/search/<int:training_id>/<int:training_no>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffBookingInputSearchView.as_view(), name='staff_booking_input_search'),
    path('staff/exbooking/input/<int:training_id>/<int:exbooking_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffExBookingInputView.as_view(), name='staff_exbooking_input'),
    path('staff/exbooking/input/<int:training_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffExBookingInputView.as_view(), name='staff_exbooking_input'),
    path('staff/closing_day', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/closing_day/<int:year>/<int:month>/<int:day>/', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/closing_day/<str:closing>/<int:year>/<int:month>/<int:day>/', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/closing_day/<int:err_cd>/<str:blackgray>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/closing_day/<str:blackgray>/<int:training_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/closing_day/<str:closing>/<int:closing_id>/<int:year>/<int:month>/<int:day>/', app_staff_views.StaffClosingDayView.as_view(), name='staff_closing_day'),
    path('staff/personal', app_staff_views.StaffPersonalView.as_view(), name='staff_personal'),
    path('staff/semipersonal', app_staff_views.StaffSemiPersonalView.as_view(), name='staff_semi_personal'),
    path('staff/ex_reserve', app_staff_views.StaffExReserveView.as_view(), name='staff_ex_reserve'),
    path('staff/work_cnt', app_staff_views.StaffWorkCntView.as_view(), name='staff_work_cnt'),
    path('staff/work_cnt/<int:year>/<int:month>/<int:day>/', app_staff_views.StaffWorkCntView.as_view(), name='staff_work_cnt'),
    path('calendar/<int:training_id>/', app_member_views.CalendarView.as_view(), name='calendar'),
    path('calendar/<int:training_id>/<int:year>/<int:month>/<int:day>/', app_member_views.CalendarView.as_view(), name='calendar'),
    path('booking/<int:pk>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_member_views.BookingView.as_view(), name='booking'),
    path('thanks', app_member_views.ThanksView.as_view(), name='thanks'),
    path('menu/mypage/cancel/cancelok', app_member_views.ThanksView.as_view(), name='cancelok'),
    path('menu/mypage', app_member_views.MypageView.as_view(), name='mypage'),
    path('menu/mypage/cancel', app_member_views.CancelView.as_view(), name='cancel'),
    path('ex_reserve/email', app_member_views.ExEmailView.as_view(), name='ex_email'),
    path('ex_reserve/certification', app_member_views.ExCertificationView.as_view(), name='ex_certification'),
    path('ex_reserve/expiration_date_invalid/<int:ex_id>/', app_member_views.ExeEpirationDateInvalidView.as_view(), name='ex_expiration_date_invalid'),
    path('ex_reserve/', app_member_views.ExReserveView.as_view(), name='ex_reserve'),
    path('ex_reserve/ex_calendar/<int:training_id>/', app_member_views.ExCalendarView.as_view(), name='ex_calendar'),
    path('ex_reserve/ex_calendar/<int:training_id>/<int:year>/<int:month>/<int:day>/', app_member_views.ExCalendarView.as_view(), name='ex_calendar'),
    path('ex_reserve/booking/<int:pk>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_member_views.ExBookingView.as_view(), name='ex_booking'),
    path('ex_reserve/ex_thanks/', app_member_views.ExThanksView.as_view(), name='ex_thanks'),
    path('ex_reserve/ex_delete/', app_member_views.ExDeleteView.as_view(), name='ex_delete'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
