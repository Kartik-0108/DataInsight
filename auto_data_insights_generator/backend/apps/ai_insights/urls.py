from django.urls import path
from . import views

app_name = 'ai_insights'

urlpatterns = [
    path('<int:dataset_id>/', views.insights_view, name='insights'),
    path('<int:dataset_id>/generate/', views.generate_insights, name='generate'),
    path('<int:dataset_id>/query/', views.smart_query, name='smart_query'),
    path('<int:dataset_id>/chat/history/', views.chat_history, name='chat_history'),
]
