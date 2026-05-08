from django.db import models
from apps.data_upload.models import UploadedDataset


class Report(models.Model):
    """Model for generated reports."""

    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
    ]

    dataset = models.ForeignKey(UploadedDataset, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='reports/%Y/%m/')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file_size = models.PositiveIntegerField(default=0)
    includes_analysis = models.BooleanField(default=True)
    includes_insights = models.BooleanField(default=True)
    includes_charts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f"{self.title} ({self.format.upper()})"

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
