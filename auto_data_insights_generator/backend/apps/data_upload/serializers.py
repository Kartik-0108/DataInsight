from rest_framework import serializers
from .models import UploadedDataset


class UploadedDatasetSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UploadedDataset
        fields = [
            'id', 'name', 'description', 'file', 'file_type',
            'file_size', 'file_size_display', 'row_count', 'column_count',
            'columns', 'status', 'uploaded_at', 'username'
        ]
        read_only_fields = ['id', 'file_type', 'file_size', 'row_count',
                            'column_count', 'columns', 'status', 'uploaded_at']
