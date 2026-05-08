from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('<int:dataset_id>/', views.analysis_dashboard, name='dashboard'),
    path('<int:dataset_id>/run/', views.run_analysis, name='run_analysis'),
    path('<int:dataset_id>/api/', views.analysis_api, name='analysis_api'),
]
