"""
WSGI config for auto_data_insights_generator project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto_data_insights_generator.settings')
application = get_wsgi_application()
