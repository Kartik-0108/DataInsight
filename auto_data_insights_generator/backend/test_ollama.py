import urllib.request
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env to get model name
load_dotenv(Path(__file__).resolve().parent / '.env')
MODEL = os.getenv('OLLAMA_MODEL', 'tinyllama')

def run_test():
    payload = {
        "model": MODEL,
        "prompt": "Hello",
        "stream": False
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        print(f"Testing with model: {MODEL}...")
        with urllib.request.urlopen(req) as resp:
            print("Success:")
            print(resp.read().decode('utf-8'))
    except Exception as e:
        print("Error:", e)
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))

if __name__ == "__main__":
    run_test()
