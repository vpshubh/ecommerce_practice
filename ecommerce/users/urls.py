from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.signup, name='register'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('order-history/', views.order_history, name='order_history'),

]