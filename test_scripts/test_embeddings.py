import requests
import json

# Test the embeddings API
url = "http://localhost:8000/generate-embeddings"
data = {
    "text": "Happy"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total chunks: {result['total_chunks']}")
        print(f"Embedding dimensions: {result['embedding_dimensions']}")
        
        # Show first chunk details
        first_chunk = result['chunks_with_embeddings'][0]
        print(f"\nFirst chunk text: {first_chunk['chunk_text'][:100]}...")
        print(f"First chunk embedding preview: {first_chunk['embedding_preview']}")
        print(f"Full embedding length: {len(first_chunk['embedding'])}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
