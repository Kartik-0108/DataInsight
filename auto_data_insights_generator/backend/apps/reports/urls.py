from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('<int:dataset_id>/', views.report_view, name='generate'),
    path('<int:dataset_id>/create/', views.generate_report, name='create'),
    path('<int:dataset_id>/download/', views.download_report, name='download'),
]
