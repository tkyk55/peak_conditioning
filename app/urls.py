from django.urls import include, path
from app import views

urlpatterns = [
    path('',views.IndexView.as_view(), name='index'),
]