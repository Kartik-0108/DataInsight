import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.data_upload.models import UploadedDataset
from .models import AnalysisResult
from .analysis_engine import AnalysisEngine


@login_required
def analysis_dashboard(request, dataset_id):
    """Display the analysis dashboard for a dataset."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)

    # Check for existing analysis
    analysis = AnalysisResult.objects.filter(dataset=dataset, analysis_type='full').first()

    return render(request, 'data_analysis/analysis_dashboard.html', {
        'dataset': dataset,
        'analysis': analysis,
    })


@login_required
def run_analysis(request, dataset_id):
    """Run full analysis on a dataset and return results as JSON."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)

    try:
        # Load the dataset
        if dataset.file_type == 'csv':
            df = pd.read_csv(dataset.file.path)
        else:
            df = pd.read_excel(dataset.file.path)

        # Run statistical analysis
        engine = AnalysisEngine(df)
        results = engine.run_full_analysis()

        # ── Generate Matplotlib plots ──────────────────────────────────────
        matplotlib_plot_urls = {}
        try:
            import matplotlib
            matplotlib.use('Agg')  # non-interactive — safe for Django
            from pathlib import Path
            from django.conf import settings as django_settings
            from .visualization_engine import AutomatedVisualizer

            plot_save_dir = Path(django_settings.MEDIA_ROOT) / 'plots' / str(dataset_id)
            viz = AutomatedVisualizer(df)
            viz.generate_all_insights(save_dir=str(plot_save_dir), show=False)

            plot_media_base = f"{django_settings.MEDIA_URL}plots/{dataset_id}/"
            plot_names = [
                'line_plot', 'histograms', 'area_plot', 'box_plots',
                'scatter_plots', 'heatmap', 'bar_chart', 'horizontal_bar',
                'stacked_bar', 'pie_charts', 'dashboard_subplots',
            ]
            for name in plot_names:
                if (plot_save_dir / f"{name}.png").exists():
                    matplotlib_plot_urls[name] = f"{plot_media_base}{name}.png"
        except Exception as plot_err:
            matplotlib_plot_urls['_error'] = str(plot_err)
        # ──────────────────────────────────────────────────────────────────

        # Save results
        analysis, created = AnalysisResult.objects.update_or_create(
            dataset=dataset,
            analysis_type='full',
            defaults={
                'results': results.get('descriptive_stats', {}),
                'summary': results.get('summary', ''),
                'charts_data': results.get('charts', {}),
            }
        )

        analysis.results = {
            'descriptive_stats': results.get('descriptive_stats', {}),
            'correlation': results.get('correlation', {}),
            'outliers': results.get('outliers', {}),
            'distribution': results.get('distribution', {}),
            'missing_data': results.get('missing_data', {}),
            'trends': results.get('trends', {}),
        }
        charts_combined = dict(results.get('charts', {}))
        charts_combined['matplotlib_plots'] = matplotlib_plot_urls
        analysis.charts_data = charts_combined
        analysis.save()

        return JsonResponse({
            'status': 'success',
            'summary': results.get('summary', ''),
            'results': analysis.results,
            'charts': charts_combined,
            'matplotlib_plots': matplotlib_plot_urls,
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=400)


@login_required
def analysis_api(request, dataset_id):
    """API endpoint to get existing analysis results."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
    analysis = AnalysisResult.objects.filter(dataset=dataset, analysis_type='full').first()

    if not analysis:
        return JsonResponse({'status': 'not_found', 'message': 'No analysis found. Run analysis first.'}, status=404)

    charts = analysis.charts_data or {}
    return JsonResponse({
        'status': 'success',
        'summary': analysis.summary,
        'results': analysis.results,
        'charts': charts,
        'matplotlib_plots': charts.get('matplotlib_plots', {}),
        'created_at': analysis.created_at.isoformat(),
    })
