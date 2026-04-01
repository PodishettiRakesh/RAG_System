import requests
import json

# Test the API
url = "http://localhost:8000/process-text"
data = {"text": "Hello world this is a test of the RAG system text processing API"}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
