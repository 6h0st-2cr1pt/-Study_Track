from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.manage_profile, name='manage_profile'),
    path('grades/new/', views.add_grade, name='add_grade'),
    path('goals/new/', views.add_goal, name='add_goal'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('data/', views.data_management, name='data_management'),
    path('subjects/<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete/', views.delete_subject, name='delete_subject'),
]
