from django.db import models
from django.contrib.auth.models import User


class UploadedDataset(models.Model):
    """Model to store uploaded dataset metadata."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    file = models.FileField(upload_to='datasets/%Y/%m/')
    file_type = models.CharField(max_length=10, default='csv')
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    row_count = models.PositiveIntegerField(default=0)
    column_count = models.PositiveIntegerField(default=0)
    columns = models.JSONField(default=list, blank=True, help_text='List of column names')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Uploaded Dataset'
        verbose_name_plural = 'Uploaded Datasets'

    def __str__(self):
        return f"{self.name} ({self.row_count}×{self.column_count})"

    @property
    def file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
