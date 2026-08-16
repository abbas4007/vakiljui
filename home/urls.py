from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),

    path('بهترین-وکیل/<path:speciality>/<path:city>/', views.SeoLandingView.as_view(), name='seo_landing'),

    path('وکلای-<path:speciality>/', views.LawyerListView.as_view(), name='lawyer_list'),
    path('وکلای-<path:speciality>-<path:city>/', views.LawyerListView.as_view(), name='lawyer_list_city'),

    path('وکیل/<path:slug>/', views.LawyerDetailView.as_view(), name='lawyer_detail'),

    path('llms.txt', views.LLMsTextView.as_view(), name='llms_txt'),
    path('subscription-plans/', views.subscription_plans, name='subscription_plans'),
    path('lawyer/register/', views.lawyer_register, name='lawyer_register'),
    path('subscribe/<int:plan_id>/', views.subscribe_view, name='subscribe'),
    path('payment-verify/', views.payment_verify, name='payment_verify'),
    path('landingpage/',views.LandingPage.as_view(),name='landingpage'),
    path('جستجو', views.LawyerSearchView.as_view(), name = 'search'),
    path('ai_match/', views.AIMatchView.as_view(), name = 'ai_match'),

    # ========== سیستم مشاوره‌ی آنلاین ==========
    path('مشاوره/', views.consultation_lawyer_list_view, name='consultation_lawyers'),
    path('مشاوره/تنظیمات/', views.consultation_settings_view, name='consultation_settings'),
    path('مشاوره/من/', views.my_consultations_view, name='my_consultations'),
    path('مشاوره/درخواست/<path:slug>/<str:format>/', views.request_consultation_view, name='request_consultation'),
    path('مشاوره/تایید-پرداخت/<int:pk>/', views.consultation_payment_verify, name='consultation_payment_verify'),
    path('مشاوره/اتاق/<int:pk>/', views.consultation_room_view, name='consultation_room'),
    path('مشاوره/اتاق/<int:pk>/ارسال/', views.consultation_send_message, name='consultation_send_message'),
    path('مشاوره/اتاق/<int:pk>/پیام‌ها/', views.consultation_poll_messages, name='consultation_poll_messages'),
    path('مشاوره/اتاق/<int:pk>/پایان/', views.consultation_complete_view, name='consultation_complete'),
]