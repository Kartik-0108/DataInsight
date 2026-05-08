import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.conf import settings
from apps.data_upload.models import UploadedDataset
from apps.data_analysis.models import AnalysisResult
from apps.ai_insights.models import AIInsight
from .models import Report
from .report_generator import ReportGenerator


@login_required
def report_view(request, dataset_id):
    """Display report generation page."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
    reports = Report.objects.filter(dataset=dataset)

    return render(request, 'reports/report_download.html', {
        'dataset': dataset,
        'reports': reports,
    })


@login_required
def generate_report(request, dataset_id):
    """Generate a PDF report for a dataset."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)

    try:
        # Get analysis results
        analysis = AnalysisResult.objects.filter(dataset=dataset, analysis_type='full').first()
        if not analysis:
            return JsonResponse({
                'status': 'error',
                'message': 'Please run analysis first before generating a report.'
            }, status=400)

        # Get AI insights
        insights = list(AIInsight.objects.filter(dataset=dataset).values(
            'title', 'insight_text', 'category', 'confidence'
        ))

        # Generate PDF
        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        filename = f"report_{dataset.id}_{dataset.name.replace(' ', '_')}.pdf"
        output_path = os.path.join(report_dir, filename)

        generator = ReportGenerator()
        generator.generate(
            dataset_name=dataset.name,
            analysis_results=analysis.results,
            insights=insights,
            output_path=output_path,
        )

        # Save report record
        file_size = os.path.getsize(output_path)
        report, created = Report.objects.update_or_create(
            dataset=dataset,
            defaults={
                'title': f'Analysis Report - {dataset.name}',
                'file': f'reports/{filename}',
                'file_size': file_size,
                'includes_analysis': True,
                'includes_insights': bool(insights),
            }
        )

        return JsonResponse({
            'status': 'success',
            'report_id': report.id,
            'download_url': f'/reports/{dataset_id}/download/',
            'file_size': report.file_size_display,
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=400)


@login_required
def download_report(request, dataset_id):
    """Download a generated report."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
    report = Report.objects.filter(dataset=dataset).order_by('-created_at').first()

    if not report or not report.file:
        return JsonResponse({'error': 'No report found.'}, status=404)

    file_path = os.path.join(settings.MEDIA_ROOT, str(report.file))
    if not os.path.exists(file_path):
        return JsonResponse({'error': 'Report file not found.'}, status=404)

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=f'{report.title}.pdf',
        content_type='application/pdf',
    )
