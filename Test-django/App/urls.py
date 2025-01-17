from django.urls import path
from App import views

urlpatterns = [
    path('', views.home_page),
    path('home/', views.home_page),
    path('generate-image/', views.generate_page),
    path('login/', views.login_page),
    path('logout/', views.logout_page),
    path('dashboard/', views.dashboard_page),
    path('view-images/', views.view_images_page),
    path('register/', views.register_page),
    path('forget-pass/', views.forget_pass_page),
    path('confirm-mail-sent/', views.confirm_mail_sent),
    path("confirm-payment/<str:payment_intent_id>/", views.confirm_payment, name="confirm_payment"),
    path('pricing/<plan>/', views.subscription_page, name='subscribe'),
    path('subscription_status/', views.subscription_status, name='status'),
    path('payment/<plan>/', views.payment_page, name='payment'),
    path('subscription-success/', views.subscription_success),
    path('change-password/<token>/', views.change_password, name='change_password'),
]