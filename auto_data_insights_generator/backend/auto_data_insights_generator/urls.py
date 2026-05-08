"""
URL configuration for auto_data_insights_generator project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
    path('users/', include('apps.users.urls')),
    path('upload/', include('apps.data_upload.urls')),
    path('analysis/', include('apps.data_analysis.urls')),
    path('insights/', include('apps.ai_insights.urls')),
    path('reports/', include('apps.reports.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
