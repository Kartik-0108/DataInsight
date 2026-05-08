import json
import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.data_upload.models import UploadedDataset
from apps.data_analysis.models import AnalysisResult
from apps.data_analysis.analysis_engine import AnalysisEngine
from .models import AIInsight
from .nlp_model import NLPInsightGenerator


@login_required
def insights_view(request, dataset_id):
    """Display AI-generated insights for a dataset."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
    insights = AIInsight.objects.filter(dataset=dataset)

    return render(request, 'ai_insights/insights_view.html', {
        'dataset': dataset,
        'insights': insights,
    })


@login_required
def generate_insights(request, dataset_id):
    """Generate AI insights for a dataset."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)

    try:
        # Get or run analysis
        analysis = AnalysisResult.objects.filter(dataset=dataset, analysis_type='full').first()

        if not analysis:
            # Run analysis first
            if dataset.file_type == 'csv':
                df = pd.read_csv(dataset.file.path)
            else:
                df = pd.read_excel(dataset.file.path)

            engine = AnalysisEngine(df)
            results = engine.run_full_analysis()

            analysis = AnalysisResult.objects.create(
                dataset=dataset,
                analysis_type='full',
                results={
                    'descriptive_stats': results.get('descriptive_stats', {}),
                    'correlation': results.get('correlation', {}),
                    'outliers': results.get('outliers', {}),
                    'distribution': results.get('distribution', {}),
                    'missing_data': results.get('missing_data', {}),
                    'trends': results.get('trends', {}),
                },
                summary=results.get('summary', ''),
                charts_data=results.get('charts', {}),
            )

        # Generate AI insights
        generator = NLPInsightGenerator()
        raw_insights = generator.generate_insights(analysis.results, dataset.name)

        # Clear old insights and save new ones
        AIInsight.objects.filter(dataset=dataset).delete()

        saved_insights = []
        for insight in raw_insights:
            obj = AIInsight.objects.create(
                dataset=dataset,
                title=insight.get('title', 'Insight'),
                insight_text=insight.get('insight_text', ''),
                category=insight.get('category', 'summary'),
                confidence=float(insight.get('confidence', 0.5)),
            )
            saved_insights.append({
                'id': obj.id,
                'title': obj.title,
                'insight_text': obj.insight_text,
                'category': obj.category,
                'confidence': obj.confidence,
            })

        return JsonResponse({
            'status': 'success',
            'insights': saved_insights,
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=400)


@login_required
@require_POST
def smart_query(request, dataset_id):
    """Handle smart query using PyTorch NLP chatbot."""
    dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)

    try:
        body = json.loads(request.body)
        question = body.get('question', '')

        if not question:
            return JsonResponse({'status': 'error', 'message': 'Please provide a question.'}, status=400)

        analysis = AnalysisResult.objects.filter(dataset=dataset, analysis_type='full').first()
        if not analysis:
            return JsonResponse({'status': 'error', 'message': 'Please run analysis first.'}, status=400)

        # Use PyTorch chatbot
        from .pytorch_chat_engine import get_chatbot
        chatbot = get_chatbot()
        if chatbot is None:
            return JsonResponse({
                'status': 'error',
                'message': 'The AI chatbot requires PyTorch which is not installed on this server. The analysis and insights features still work fully.'
            }, status=503)
        session_id = f"{request.session.session_key or 'anon'}_{dataset_id}"
        result = chatbot.chat(question, analysis.results, dataset.name, session_id)

        return JsonResponse({
            'status': 'success',
            'question': question,
            'answer': result['answer'],
            'intent': result['intent'],
            'confidence': result['confidence'],
            'context_turns': result['context_turns'],
            'focus_column': result.get('focus_column'),
            'suggested_actions': result.get('suggested_actions', []),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def chat_history(request, dataset_id):
    """Return conversation history for this dataset session."""
    from .pytorch_chat_engine import get_chatbot
    chatbot = get_chatbot()
    session_id = f"{request.session.session_key or 'anon'}_{dataset_id}"
    history = chatbot.get_history(session_id)
    return JsonResponse({'status': 'success', 'history': history})
