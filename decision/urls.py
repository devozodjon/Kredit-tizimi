from django.urls import path
from . import views

app_name = 'tree'


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # API endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/attributes/', views.api_attributes, name='api_attributes'),
    path('api/attribute-values/', views.api_attribute_values, name='api_attribute_values'),
    path('api/rules/', views.api_rules, name='api_rules'),
    path('api/applicants/', views.api_applicants, name='api_applicants'),

    # Delete endpoints
    path('api/attributes/<int:pk>/delete/', views.api_attribute_delete, name='api_attribute_delete'),
    path('api/attribute-values/<int:pk>/delete/', views.api_attribute_value_delete, name='api_attribute_value_delete'),
    path('api/rules/<int:pk>/delete/', views.api_rule_delete, name='api_rule_delete'),
    path('api/applicants/<int:pk>/delete/', views.api_applicant_delete, name='api_applicant_delete'),
]