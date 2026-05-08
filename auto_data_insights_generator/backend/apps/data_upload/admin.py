from django.contrib import admin
from .models import UploadedDataset


@admin.register(UploadedDataset)
class UploadedDatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'file_type', 'row_count', 'column_count', 'status', 'uploaded_at')
    list_filter = ('status', 'file_type', 'uploaded_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('row_count', 'column_count', 'file_size', 'columns')
