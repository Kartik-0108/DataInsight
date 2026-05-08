from django.db import models
from apps.data_upload.models import UploadedDataset


class AIInsight(models.Model):
    """Stores AI-generated insights for a dataset."""

    CATEGORY_CHOICES = [
        ('trend', 'Trend'),
        ('correlation', 'Correlation'),
        ('anomaly', 'Anomaly'),
        ('summary', 'Summary'),
        ('recommendation', 'Recommendation'),
    ]

    dataset = models.ForeignKey(UploadedDataset, on_delete=models.CASCADE, related_name='insights')
    title = models.CharField(max_length=255, default='')
    insight_text = models.TextField(help_text='AI-generated insight text')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='summary')
    confidence = models.FloatField(default=0.0, help_text='Confidence score 0-1')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'

    def __str__(self):
        return f"{self.title} - {self.dataset.name}"
