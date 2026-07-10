from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),

    # صفحات لندینگ (با path به جای slug برای پشتیبانی از فارسی)
    path('بهترین-وکیل/<path:speciality>/<path:city>/', views.SeoLandingView.as_view(), name='seo_landing'),

    # لیست وکلا (با پشتیبانی از فارسی)
    path('وکلای-<path:speciality>/', views.LawyerListView.as_view(), name='lawyer_list'),
    path('وکلای-<path:speciality>-<path:city>/', views.LawyerListView.as_view(), name='lawyer_list_city'),

    # جزئیات وکیل (فارسی)
    path('وکیل/<path:slug>/', views.LawyerDetailView.as_view(), name='lawyer_detail'),

    # صفحات سیستمی
    path('llms.txt', views.LLMsTextView.as_view(), name='llms_txt'),
    path('subscription-plans/', views.subscription_plans, name='subscription_plans'),
    path('lawyer/register/', views.lawyer_register, name='lawyer_register'),
    path('subscribe/<int:plan_id>/', views.subscribe_view, name='subscribe'),
    path('payment-verify/', views.payment_verify, name='payment_verify'),
    path('landingpage/',views.LandingPage.as_view(),name='landingpage'),
]