import os
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UploadedDataset


@login_required
def upload_view(request):
    """Display upload page and handle file uploads."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('dataset_file')
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('data_upload:upload')

        # Validate file type
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            messages.error(request, 'Only CSV and Excel files are supported.')
            return redirect('data_upload:upload')

        # Create dataset record
        dataset = UploadedDataset(
            user=request.user,
            name=request.POST.get('name', uploaded_file.name),
            description=request.POST.get('description', ''),
            file=uploaded_file,
            file_type='csv' if file_ext == '.csv' else 'excel',
            file_size=uploaded_file.size,
        )
        dataset.save()

        # Process the file to extract metadata
        try:
            if file_ext == '.csv':
                df = pd.read_csv(dataset.file.path)
            else:
                df = pd.read_excel(dataset.file.path)

            dataset.row_count = len(df)
            dataset.column_count = len(df.columns)
            dataset.columns = list(df.columns)
            dataset.status = 'completed'
            dataset.save()
            messages.success(request, f'Dataset "{dataset.name}" uploaded successfully! ({dataset.row_count} rows, {dataset.column_count} columns)')
        except Exception as e:
            dataset.status = 'failed'
            dataset.save()
            messages.error(request, f'Error processing file: {str(e)}')

        return redirect('data_upload:upload')

    # GET request — show upload page with user's datasets
    datasets = UploadedDataset.objects.filter(user=request.user)
    return render(request, 'data_upload/upload.html', {'datasets': datasets})


@login_required
def dataset_detail_api(request, pk):
    """API endpoint to get dataset preview data."""
    dataset = get_object_or_404(UploadedDataset, pk=pk, user=request.user)

    try:
        if dataset.file_type == 'csv':
            df = pd.read_csv(dataset.file.path)
        else:
            df = pd.read_excel(dataset.file.path)

        # Return first 100 rows as preview
        preview = df.head(100)
        
        # Convert NaN to None for JSON serialization
        preview_clean = preview.where(pd.notnull(preview), None)
        stats_clean = df.describe(include='all').where(pd.notnull(df.describe(include='all')), None)
        
        data = {
            'name': dataset.name,
            'rows': dataset.row_count,
            'columns': dataset.column_count,
            'column_names': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'preview': preview_clean.to_dict(orient='records'),
            'stats': stats_clean.to_dict(),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def dataset_delete(request, pk):
    """Delete a dataset."""
    dataset = get_object_or_404(UploadedDataset, pk=pk, user=request.user)
    name = dataset.name
    # Delete the file from storage
    if dataset.file and os.path.exists(dataset.file.path):
        os.remove(dataset.file.path)
    dataset.delete()
    messages.success(request, f'Dataset "{name}" deleted successfully.')
    return redirect('data_upload:upload')


@login_required
def compare_view(request):
    """Display dataset comparison page."""
    datasets = UploadedDataset.objects.filter(user=request.user, status='completed')
    return render(request, 'data_upload/compare.html', {'datasets': datasets})


@login_required
def compare_api(request):
    """API: compare two datasets side-by-side."""
    from apps.data_analysis.models import AnalysisResult

    id1 = request.GET.get('dataset1')
    id2 = request.GET.get('dataset2')
    if not id1 or not id2:
        return JsonResponse({'error': 'Two dataset IDs required.'}, status=400)

    ds1 = get_object_or_404(UploadedDataset, pk=id1, user=request.user)
    ds2 = get_object_or_404(UploadedDataset, pk=id2, user=request.user)

    a1 = AnalysisResult.objects.filter(dataset=ds1, analysis_type='full').first()
    a2 = AnalysisResult.objects.filter(dataset=ds2, analysis_type='full').first()

    def summarize(ds, analysis):
        if not analysis:
            return {'name': ds.name, 'error': 'Run analysis first'}
        r = analysis.results or {}
        desc = r.get('descriptive_stats', {})
        shape = desc.get('shape', {})
        missing = r.get('missing_data', {})
        corr = r.get('correlation', {})
        outliers = r.get('outliers', {})
        trends = r.get('trends', {})
        numeric = desc.get('numeric', desc.get('numeric_stats', {}))

        # Collect mean values per column
        means = {}
        for col, stats in numeric.items():
            if isinstance(stats, dict) and 'mean' in stats:
                means[col] = round(float(stats['mean']), 2)

        return {
            'name': ds.name,
            'rows': shape.get('rows', 0),
            'columns': shape.get('columns', 0),
            'completeness': missing.get('completeness', 100),
            'total_missing': missing.get('total_missing_cells', 0),
            'top_correlations': corr.get('top_correlations', [])[:5],
            'outlier_total': sum(
                v.get('count', 0) for v in outliers.get('iqr_method', {}).values()
                if isinstance(v, dict)
            ),
            'trend_count': len(trends),
            'means': means,
        }

    return JsonResponse({
        'dataset1': summarize(ds1, a1),
        'dataset2': summarize(ds2, a2),
    })

