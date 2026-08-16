from django.urls import path

from . import views


app_name = 'accounts'


urlpatterns = [

    path(
        'ثبت-نام/',
        views.SignupView.as_view(),
        name='signup'
    ),

    path(
        'ورود/',
        views.login_view,
        name='login'
    ),

    path(
        'درخواست-احراز-وکالت/',
        views.LawyerVerificationCreateView.as_view(),
        name='lawyer_verification'
    ),

    path(
        'درخواست-احراز-وکالت/ثبت-شد/',
        views.LawyerVerificationSuccessView.as_view(),
        name='lawyer_verification_success'
    ),

    path(
        'وضعیت-احراز-وکالت/',
        views.LawyerVerificationStatusView.as_view(),
        name='lawyer_verification_status'
    ),
]