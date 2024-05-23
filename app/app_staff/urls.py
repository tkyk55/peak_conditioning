from django.urls import include, path
from app.app_staff import views

urlpatterns = [
    path('',views.IndexView.as_view(), name='index'),
]