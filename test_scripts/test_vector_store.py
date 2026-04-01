import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

def test_vector_storage():
    """Test the vector storage functionality."""
    
    print("=== TESTING VECTOR STORAGE ===")
    
    # Test 1: Store chunks
    print("\n1. Storing chunks...")
    store_url = f"{BASE_URL}/store-chunks"
    test_text = """
    Retrieval-Augmented Generation (RAG) is a powerful technique that combines large language models 
    with external knowledge sources. Instead of relying only on pre-trained data, RAG retrieves 
    relevant information from a document store and uses it to generate more accurate responses.
    """
    
    try:
        response = requests.post(store_url, json={"text": test_text})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Chunks added: {result['chunks_added']}")
            print(f"Total chunks: {result['total_chunks']}")
            print(f"Stats: {result['stats']}")
            
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error storing chunks: {e}")
    
    # Test 2: Get stats
    print("\n2. Getting store stats...")
    stats_url = f"{BASE_URL}/store-stats"
    
    try:
        response = requests.get(stats_url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print("Store Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    # Test 3: Get stored chunks
    print("\n3. Getting stored chunks...")
    chunks_url = f"{BASE_URL}/stored-chunks"
    
    try:
        response = requests.get(chunks_url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Total chunks stored: {result['total']}")
            
            # Show first chunk
            if result['chunks']:
                first_chunk = result['chunks'][0]
                print(f"\nFirst chunk preview:")
                print(f"  ID: {first_chunk['chunk_id']}")
                print(f"  Words: {first_chunk['words']}")
                print(f"  Text: {first_chunk['text'][:100]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error getting chunks: {e}")

if __name__ == "__main__":
    test_vector_storage()
