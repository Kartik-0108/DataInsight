from django.db import models
from apps.data_upload.models import UploadedDataset


class AnalysisResult(models.Model):
    """Stores results of data analysis for a dataset."""

    ANALYSIS_TYPES = [
        ('descriptive', 'Descriptive Statistics'),
        ('correlation', 'Correlation Analysis'),
        ('outlier', 'Outlier Detection'),
        ('trend', 'Trend Detection'),
        ('distribution', 'Distribution Analysis'),
        ('full', 'Full Analysis'),
    ]

    dataset = models.ForeignKey(UploadedDataset, on_delete=models.CASCADE, related_name='analysis_results')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES, default='full')
    results = models.JSONField(default=dict, help_text='JSON analysis output')
    summary = models.TextField(blank=True, default='', help_text='Human-readable summary')
    charts_data = models.JSONField(default=dict, help_text='Chart.js configuration data')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'

    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.dataset.name}"
