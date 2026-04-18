from typing import List, Dict, Any, Tuple
import json
import time
import re
from src.services.vector_store_service import VectorStoreService
from src.services.llm_service import LLMService


class EvaluationService:
    """Comprehensive RAG evaluation system with automated metrics."""
    
    def __init__(self, vector_store: VectorStoreService, llm_service: LLMService):
        """
        Initialize EvaluationService.
        
        Args:
            vector_store: VectorStoreService instance for retrieval
            llm_service: LLMService instance for generation
        """
        self.vector_store = vector_store
        self.llm_service = llm_service
    
    def evaluate_retrieval(self, relevant_chunk_ids: List[int], retrieved_chunks: List[Dict], k: int) -> Dict[str, float]:
        """
        Evaluate retrieval quality using automated metrics.
        
        Args:
            relevant_chunk_ids: List of ground truth relevant chunk IDs
            retrieved_chunks: List of retrieved chunks with metadata
            k: Number of chunks retrieved
            
        Returns:
            Dictionary with retrieval metrics
        """
        # Extract chunk IDs from retrieved results
        retrieved_ids = [chunk.get('chunk_id', -1) for chunk in retrieved_chunks]
        
        # Calculate relevant retrieved chunks
        relevant_retrieved = sum(1 for chunk_id in retrieved_ids if chunk_id in relevant_chunk_ids)
        
        # Precision@K: relevant_retrieved / k
        precision_at_k = relevant_retrieved / k if k > 0 else 0.0
        
        # Hit Rate: 1 if at least one relevant chunk retrieved, else 0
        hit_rate = 1.0 if relevant_retrieved > 0 else 0.0
        
        # Average Distance: mean similarity score of retrieved chunks
        distances = [chunk.get('similarity_score', 0) for chunk in retrieved_chunks]
        avg_distance = sum(distances) / len(distances) if distances else 0.0
        
        return {
            'precision_at_k': precision_at_k,
            'hit_rate': hit_rate,
            'avg_distance': avg_distance,
            'relevant_retrieved': relevant_retrieved,
            'total_retrieved': k
        }
    
    def evaluate_generation(self, ground_truth: str, generated_response: str, expected_keywords: List[str]) -> Dict[str, Any]:
        """
        Evaluate generation quality using automated metrics.
        
        Args:
            ground_truth: Ground truth answer
            generated_response: Generated response from RAG
            expected_keywords: List of expected keywords
            
        Returns:
            Dictionary with generation metrics
        """
        # Exact Match: check if ground truth is contained in response
        exact_match = 1.0 if ground_truth.lower() in generated_response.lower() else 0.0
        
        # Keyword Score: percentage of expected keywords found in response
        response_lower = generated_response.lower()
        matched_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
        keyword_score = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0.0
        
        # Answer Length: character count of generated response
        answer_length = len(generated_response)
        
        return {
            'exact_match': exact_match,
            'keyword_score': keyword_score,
            'answer_length': answer_length,
            'matched_keywords': matched_keywords,
            'total_keywords': len(expected_keywords)
        }
    
    def detect_hallucination(self, generated_response: str, context_chunks: List[str]) -> Dict[str, Any]:
        """
        Detect hallucinations by checking if response is grounded in context.
        
        Args:
            generated_response: Generated response from RAG
            context_chunks: List of context chunks used for generation
            
        Returns:
            Dictionary with hallucination detection results
        """
        # Combine all context into single string
        combined_context = ' '.join(context_chunks).lower()
        
        # Split response into sentences/phrases
        response_phrases = [phrase.strip() for phrase in generated_response.split('.') if phrase.strip()]
        
        # Check each phrase for grounding in context
        grounded_phrases = 0
        ungrounded_phrases = []
        
        for phrase in response_phrases:
            phrase_lower = phrase.lower()
            # Check if key phrases from response appear in context
            words_in_phrase = phrase_lower.split()
            words_found_in_context = sum(1 for word in words_in_phrase if word in combined_context)
            
            # Consider phrase grounded if at least 30% of words appear in context
            if len(words_in_phrase) > 0 and (words_found_in_context / len(words_in_phrase)) >= 0.3:
                grounded_phrases += 1
            else:
                ungrounded_phrases.append(phrase)
        
        # Hallucination detected if less than 70% of phrases are grounded
        hallucination_score = grounded_phrases / len(response_phrases) if response_phrases else 0.0
        hallucination_detected = hallucination_score < 0.7
        
        return {
            'hallucination_detected': hallucination_detected,
            'grounding_score': hallucination_score,
            'grounded_phrases': grounded_phrases,
            'total_phrases': len(response_phrases),
            'ungrounded_phrases': ungrounded_phrases[:3]  # Limit to first 3 for readability
        }
    
    def evaluate_single_query(self, query_data: Dict[str, Any], k: int = 3) -> Dict[str, Any]:
        """
        Evaluate a single query end-to-end.
        
        Args:
            query_data: Dictionary containing question, ground_truth, expected_keywords, relevant_chunk_ids
            k: Number of chunks to retrieve
            
        Returns:
            Dictionary with comprehensive evaluation results
        """
        start_time = time.time()
        
        # Extract query information
        question = query_data['question']
        ground_truth = query_data['ground_truth']
        expected_keywords = query_data['expected_keywords']
        relevant_chunk_ids = query_data['relevant_chunk_ids']
        
        # Step 1: Retrieve relevant chunks
        retrieved_chunks = self.vector_store.search_similar(question, k)
        
        # Step 2: Generate response
        llm_result = self.llm_service.generate_response(question, retrieved_chunks, 200)
        generated_response = llm_result.get('response', '')
        
        # Step 3: Evaluate retrieval
        retrieval_metrics = self.evaluate_retrieval(relevant_chunk_ids, retrieved_chunks, k)
        
        # Step 4: Evaluate generation
        generation_metrics = self.evaluate_generation(ground_truth, generated_response, expected_keywords)
        
        # Step 5: Detect hallucinations
        context_texts = [chunk.get('chunk_text', '') for chunk in retrieved_chunks]
        hallucination_metrics = self.detect_hallucination(generated_response, context_texts)
        
        # Step 6: Calculate overall score
        overall_score = (
            retrieval_metrics['precision_at_k'] * 0.3 +
            retrieval_metrics['hit_rate'] * 0.2 +
            generation_metrics['keyword_score'] * 0.3 +
            (1.0 - hallucination_metrics['grounding_score']) * 0.2
        ) * 10  # Scale to 0-10
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            'question': question,
            'ground_truth': ground_truth,
            'generated_response': generated_response,
            'retrieval_metrics': retrieval_metrics,
            'generation_metrics': generation_metrics,
            'hallucination_metrics': hallucination_metrics,
            'overall_score': overall_score,
            'response_time': response_time,
            'retrieved_chunks': retrieved_chunks[:2]  # Limit for readability
        }
    
    def evaluate_dataset(self, dataset_path: str, k: int = 3) -> Dict[str, Any]:
        """
        Evaluate entire dataset and generate aggregate metrics.
        
        Args:
            dataset_path: Path to evaluation dataset JSON file
            k: Number of chunks to retrieve for each query
            
        Returns:
            Dictionary with comprehensive evaluation results
        """
        # Load evaluation dataset
        with open(dataset_path, 'r') as f:
            evaluation_data = json.load(f)
        
        # Evaluate each query
        individual_results = []
        total_start_time = time.time()
        
        for query_data in evaluation_data:
            result = self.evaluate_single_query(query_data, k)
            individual_results.append(result)
        
        total_end_time = time.time()
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(individual_results)
        
        return {
            'individual_results': individual_results,
            'aggregate_metrics': aggregate_metrics,
            'total_queries': len(evaluation_data),
            'total_evaluation_time': total_end_time - total_start_time,
            'k_value': k
        }
    
    def _calculate_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate aggregate metrics from individual results.
        
        Args:
            results: List of individual evaluation results
            
        Returns:
            Dictionary with aggregate metrics
        """
        if not results:
            return {}
        
        # Calculate averages
        avg_precision = sum(r['retrieval_metrics']['precision_at_k'] for r in results) / len(results)
        hit_rate = sum(r['retrieval_metrics']['hit_rate'] for r in results) / len(results)
        avg_keyword_score = sum(r['generation_metrics']['keyword_score'] for r in results) / len(results)
        hallucination_rate = sum(1 for r in results if r['hallucination_metrics']['hallucination_detected']) / len(results)
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        avg_overall_score = sum(r['overall_score'] for r in results) / len(results)
        
        return {
            'avg_precision_at_k': avg_precision,
            'hit_rate_percentage': hit_rate * 100,
            'avg_keyword_score': avg_keyword_score,
            'hallucination_rate_percentage': hallucination_rate * 100,
            'avg_response_time_seconds': avg_response_time,
            'avg_overall_score': avg_overall_score
        }
