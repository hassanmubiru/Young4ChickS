from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register_farmer/', views.register_farmer, name='register_farmer'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('farmer_dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('sales_dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('make_request/', views.make_request, name='make_request'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('manage_stock/', views.manage_stock, name='manage_stock'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('approve_request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject_request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('complete_sale/<int:request_id>/', views.complete_sale, name='complete_sale'),
    path('request_status/<int:request_id>/', views.request_status, name='request_status')
]
