from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('ثبت-نام/', views.SignupView.as_view(), name='signup'),
    path('ورود/', views.login_view, name='login'),
    path('خروج/', views.logout_view, name='logout'),
]