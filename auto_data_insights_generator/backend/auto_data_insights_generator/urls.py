"""
URL configuration for auto_data_insights_generator project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve


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

# Always serve media files (uploaded datasets & generated plots)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
