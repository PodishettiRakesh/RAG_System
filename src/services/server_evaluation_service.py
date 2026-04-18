"""
Server-based Evaluation Service for RAG System

This service uses the RAG server API for evaluation instead of local services.
"""

import requests
import time
from typing import List, Dict, Any
from src.services.llm_service import LLMService


class ServerEvaluationService:
    """Evaluation service that uses RAG server API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.llm_service = LLMService()
    
    def query_server(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Query the RAG server."""
        try:
            response = requests.post(
                f"{self.base_url}/rag",
                json={"query": question, "k": k, "max_length": 200},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying server: {e}")
            return None
    
    def evaluate_single_query(self, question: str, expected_answer: str, k: int = 3) -> Dict[str, Any]:
        """Evaluate a single query using server API."""
        start_time = time.time()
        
        # Get response from server
        server_response = self.query_server(question, k)
        if not server_response:
            return {
                "question": question,
                "error": "Failed to get response from server",
                "retrieval_metrics": {"precision_at_k": 0, "hit_rate": 0, "avg_distance": 0},
                "generation_metrics": {"exact_match": 0, "keyword_score": 0, "answer_length": 0},
                "hallucination_metrics": {"hallucination_detected": True},
                "overall_score": 0,
                "response_time": time.time() - start_time
            }
        
        answer = server_response.get("response", "")
        retrieved_chunks = server_response.get("retrieved_chunks", [])
        response_time = time.time() - start_time
        
        # Check if response indicates no relevant chunks found
        if "No relevant information found" in answer or len(answer.strip()) == 0:
            return {
                "question": question,
                "answer": "No relevant information found in stored chunks",
                "retrieved_chunks": [],
                "retrieval_metrics": {"precision_at_k": 0, "hit_rate": 0, "avg_distance": 0},
                "generation_metrics": {"exact_match": 0, "keyword_score": 0, "answer_length": 0},
                "hallucination_metrics": {"hallucination_detected": False},
                "overall_score": 0,
                "response_time": response_time,
                "k": k,
                "note": "Query filtered out by similarity threshold"
            }
        
        # Calculate metrics
        retrieval_metrics = self._calculate_retrieval_metrics(retrieved_chunks, expected_answer)
        generation_metrics = self._calculate_generation_metrics(answer, expected_answer)
        hallucination_metrics = self._calculate_hallucination_metrics(answer, retrieved_chunks)
        
        # Calculate overall score
        overall_score = (
            retrieval_metrics["precision_at_k"] * 3 +
            generation_metrics["keyword_score"] * 2 +
            (1 if not hallucination_metrics["hallucination_detected"] else 0) * 3 +
            generation_metrics["exact_match"] * 2
        )
        
        return {
            "question": question,
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "retrieval_metrics": retrieval_metrics,
            "generation_metrics": generation_metrics,
            "hallucination_metrics": hallucination_metrics,
            "overall_score": min(overall_score, 10),
            "response_time": response_time,
            "k": k
        }
    
    def _calculate_retrieval_metrics(self, retrieved_chunks: List[str], expected_answer: str) -> Dict[str, float]:
        """Calculate retrieval metrics."""
        if not retrieved_chunks:
            return {"precision_at_k": 0, "hit_rate": 0, "avg_distance": 0}
        
        # Simple precision calculation (can be improved)
        relevant_chunks = 0
        for chunk in retrieved_chunks:
            # Extract text from chunk dictionaries
            if isinstance(chunk, dict):
                chunk_text = chunk.get("chunk_text", "")
            else:
                chunk_text = str(chunk)
            
            # Check if chunk contains relevant keywords
            if any(word.lower() in chunk_text.lower() for word in expected_answer.split()[:3]):
                relevant_chunks += 1
        
        precision_at_k = relevant_chunks / len(retrieved_chunks)
        hit_rate = 1 if relevant_chunks > 0 else 0
        
        # Calculate actual average distance from retrieved chunks
        distances = []
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                similarity_score = chunk.get("similarity_score", 0)
                if similarity_score is not None:
                    distances.append(similarity_score)
        
        avg_distance = sum(distances) / len(distances) if distances else 0
        
        return {
            "precision_at_k": precision_at_k,
            "hit_rate": hit_rate,
            "avg_distance": avg_distance
        }
    
    def _calculate_generation_metrics(self, answer: str, expected_answer: str) -> Dict[str, Any]:
        """Calculate generation metrics."""
        # Exact match
        exact_match = 1 if answer.strip().lower() == expected_answer.strip().lower() else 0
        
        # Keyword score
        expected_words = set(expected_answer.lower().split())
        answer_words = set(answer.lower().split())
        
        if len(expected_words) == 0:
            keyword_score = 0
        else:
            keyword_score = len(expected_words & answer_words) / len(expected_words)
        
        return {
            "exact_match": exact_match,
            "keyword_score": keyword_score,
            "answer_length": len(answer)
        }
    
    def _calculate_hallucination_metrics(self, answer: str, retrieved_chunks: List[str]) -> Dict[str, bool]:
        """Calculate hallucination metrics."""
        if not retrieved_chunks or not answer.strip():
            return {"hallucination_detected": True}
        
        # More realistic hallucination detection
        answer_words = set(answer.lower().split())
        chunk_words = set()
        
        # Extract text from chunk dictionaries
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                chunk_text = chunk.get("chunk_text", "")
            else:
                chunk_text = str(chunk)
            
            if chunk_text:  # Only add words from non-empty chunks
                chunk_words.update(chunk_text.lower().split())
        
        # Debug logging (disabled for clean output)
        DEBUG = False
        if DEBUG:
            print(f"DEBUG: Answer words: {answer_words}")
            print(f"DEBUG: Chunk words: {chunk_words}")
            print(f"DEBUG: Retrieved chunks: {retrieved_chunks}")
        
        # If more than 70% of answer words are not in chunks, flag as hallucination
        novel_words = answer_words - chunk_words
        content_overlap = len(answer_words & chunk_words) / len(answer_words) if answer_words else 0
        
        hallucination_detected = len(novel_words) > len(answer_words) * 0.7
        if content_overlap >= 0.3:  # At least 30% overlap
            hallucination_detected = False
        
        return {"hallucination_detected": hallucination_detected}
    
    def evaluate_dataset(self, dataset_path: str, k: int = 3) -> Dict[str, Any]:
        """Evaluate entire dataset using server API."""
        import json
        
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        
        individual_results = []
        total_start_time = time.time()
        
        for item in dataset:
            result = self.evaluate_single_query(item["question"], item["ground_truth"], k)
            individual_results.append(result)
        
        total_time = time.time() - total_start_time
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(individual_results)
        
        return {
            "individual_results": individual_results,
            "aggregate_metrics": aggregate_metrics,
            "total_queries": len(individual_results),
            "total_evaluation_time": total_time
        }
    
    def _calculate_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from individual results."""
        if not results:
            return {
                "avg_precision_at_k": 0,
                "hit_rate_percentage": 0,
                "avg_keyword_score": 0,
                "hallucination_rate_percentage": 100,
                "avg_response_time_seconds": 0,
                "avg_overall_score": 0
            }
        
        total_precision = sum(r["retrieval_metrics"]["precision_at_k"] for r in results)
        hit_count = sum(1 for r in results if r["retrieval_metrics"]["hit_rate"] > 0)
        total_keyword_score = sum(r["generation_metrics"]["keyword_score"] for r in results)
        hallucination_count = sum(1 for r in results if r["hallucination_metrics"]["hallucination_detected"])
        total_response_time = sum(r["response_time"] for r in results)
        total_overall_score = sum(r["overall_score"] for r in results)
        
        n = len(results)
        
        return {
            "avg_precision_at_k": total_precision / n,
            "hit_rate_percentage": (hit_count / n) * 100,
            "avg_keyword_score": total_keyword_score / n,
            "hallucination_rate_percentage": (hallucination_count / n) * 100,
            "avg_response_time_seconds": total_response_time / n,
            "avg_overall_score": total_overall_score / n
        }
