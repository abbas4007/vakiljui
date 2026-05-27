from django.urls import re_path
from . import views

app_name = 'accounts'

urlpatterns = [
    re_path(r'^ثبت-نام/$', views.SignupView.as_view(), name='signup'),
    re_path(r'^ورود/$', views.login_view, name='login'),
    re_path(r'^خروج/$', views.logout_view, name='logout'),
]
