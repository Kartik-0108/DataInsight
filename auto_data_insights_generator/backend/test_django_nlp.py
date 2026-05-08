import os
import sys

def run_test():
    # Setup Django Environment
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto_data_insights_generator.settings')

    import django
    django.setup()

    from apps.ai_insights.nlp_model import NLPInsightGenerator

    nlp = NLPInsightGenerator()

    analysis_results = {
        'descriptive_stats': {'shape': {'rows': 100, 'columns': 5}}
    }

    try:
        print("Asking question...")
        ans = nlp.ask_question("What is the data shape?", analysis_results, "Test")
        print("Answer received:")
        print(ans)
    except Exception as e:
        print("Caught at top:", e)

if __name__ == "__main__":
    run_test()
