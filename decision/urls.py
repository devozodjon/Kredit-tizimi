from django.urls import path
from . import views

app_name = 'decision'

urlpatterns = [
    path('', views.user_form, name='user_form'),
    path('api/find-rule/', views.find_matching_rule, name='find_rule'),
    path('api/check-chain/', views.check_chain_rule, name='check_chain'),  # YANGI
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('reset/', views.reset_form, name='reset'),
]