# urls.py

from django.urls import path
from . import views

app_name = 'decision'

urlpatterns = [
    # User qismi
    path('', views.user_form, name='user_form'),
    path('api/find-rule/', views.find_matching_rule, name='find_rule'),
    path('api/check-chain/', views.check_chain_rule, name='check_chain'),
    path('reset/', views.reset_form, name='reset'),

    # Admin authentication
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),

    # Attributes CRUD API
    path('api/attributes/', views.get_attributes, name='get_attributes'),
    path('api/attributes/create/', views.create_attribute, name='create_attribute'),
    path('api/attributes/<int:attr_id>/update/', views.update_attribute, name='update_attribute'),
    path('api/attributes/<int:attr_id>/delete/', views.delete_attribute, name='delete_attribute'),

    # Attribute Values CRUD API
    path('api/values/', views.get_values, name='get_values'),
    path('api/values/create/', views.create_value, name='create_value'),
    path('api/values/<int:val_id>/update/', views.update_value, name='update_value'),
    path('api/values/<int:val_id>/delete/', views.delete_value, name='delete_value'),

    # Rules CRUD API
    path('api/rules/', views.get_rules, name='get_rules'),
    path('api/rules/create/', views.create_rule, name='create_rule'),
    path('api/rules/<int:rule_id>/update/', views.update_rule, name='update_rule'),
    path('api/rules/<int:rule_id>/delete/', views.delete_rule, name='delete_rule'),
]