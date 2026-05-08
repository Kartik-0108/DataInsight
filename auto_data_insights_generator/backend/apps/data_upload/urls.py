from django.urls import path
from . import views

app_name = 'data_upload'

urlpatterns = [
    path('', views.upload_view, name='upload'),
    path('compare/', views.compare_view, name='compare'),
    path('compare/api/', views.compare_api, name='compare_api'),
    path('api/<int:pk>/', views.dataset_detail_api, name='dataset_detail_api'),
    path('delete/<int:pk>/', views.dataset_delete, name='dataset_delete'),
]
