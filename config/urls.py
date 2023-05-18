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
from app import views as app_views
import debug_toolbar

app_name = 'accounts'
urlpatterns = [
    path('admin/', admin.site.urls),
    #path('',TemplateView.as_view(template_name='home.html'), name='home'),
    path('',include('app.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LoginView.as_view(), name='logout'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('reserve/', views.ReserveView.as_view(), name='reserve'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('staff/', app_views.StaffView.as_view(), name='staff'),
    path('staff/calendar/<int:year>/<int:month>/<int:day>/', app_views.StaffCalendarView.as_view(), name='staff_calendar'),
    path('staff/member/', app_views.StaffMemberView.as_view(), name='member'),
    path('staff/member/list', app_views.StaffMemberListView.as_view(), name='member_list'),
    path('staff/member/imput', app_views.StaffMemberInputView.as_view(), name='member_input'),
    path('staff/member/imput/ok', app_views.StaffMemberInputOkView.as_view(), name='member_input_ok'),
    path('staff/notification', app_views.StaffNotificationView.as_view(), name='notification'),
    path('staff/holiday', app_views.StaffHolidayView.as_view(), name='holiday'),
    path('staff/notification/ok', app_views.StaffNotificationOkView.as_view(), name='notification_ok'),
    path('calendar/<int:pk>/', app_views.CalendarView.as_view(), name='calendar'),
    path('calendar/<int:pk>/<int:year>/<int:month>/<int:day>/', app_views.CalendarView.as_view(), name='calendar'),
    path('booking/<int:pk>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', app_views.BookingView.as_view(), name='booking'),
    path('thanks', app_views.ThanksView.as_view(), name='thanks'),
    path('menu/mypage/cancel/cancelok', app_views.ThanksView.as_view(), name='cancelok'),
    path('menu/mypage', app_views.MypageView.as_view(), name='mypage'),
    path('menu/mypage/cancel', app_views.CancelView.as_view(), name='cancel'),
    path('ex_reserve/', app_views.ExReserveView.as_view(), name='ex_reserve'),
    path('ex_reserve/ex_calendar/<int:pk>/', app_views.ExCalendarView.as_view(), name='ex_calendar'),
    path('ex_reserve/ex_calendar/<int:pk>/<int:year>/<int:month>/<int:day>/', app_views.ExCalendarView.as_view(), name='ex_calendar'),
    path('ex_reserve/booking/<int:pk>/<int:year>/<int:month>/<int:day>/<int:hour>/', app_views.ExBookingView.as_view(), name='ex_booking'),
    path('ex_reserve/ex_thanks/', app_views.ExThanksView.as_view(), name='ex_thanks'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
