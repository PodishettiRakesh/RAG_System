"""SSE streaming orchestrator for the RAG pipeline."""

import time
from typing import AsyncIterator, List, Dict, Any

from fastapi import Request

from src.services.llm_service import LLMService
from src.services.vector_store_service import VectorStoreService
from src.services.evaluation_service import EvaluationService
from src.utils.sse import format_sse, sse_error, utc_timestamp
from src.utils.rag_retrieval import (
    filter_search_results,
    compute_retrieval_confidence,
    SIMILARITY_THRESHOLD,
)
from src.utils.observability import observability


class RagStreamService:
    """Orchestrates retrieval, generation, and evaluation as SSE events."""

    def __init__(self, vector_store: VectorStoreService, llm_service: LLMService):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self._evaluator = EvaluationService(vector_store, llm_service)

    async def stream(
        self,
        http_request: Request,
        query: str,
        k: int,
        max_length: int,
    ) -> AsyncIterator[str]:
        """
        Yield SSE-formatted events for the full RAG pipeline.

        Args:
            http_request: FastAPI request (for disconnect detection)
            query: User query
            k: Number of chunks to retrieve
            max_length: Max generation length
        """
        pipeline_start = time.time()
        search_start = 0.0
        search_end = 0.0
        llm_start = 0.0
        llm_end = 0.0
        search_results: List[Dict] = []
        full_response = ""

        try:
            yield format_sse(
                "retrieval_started",
                {"query": query, "k": k, "timestamp": utc_timestamp()},
            )

            if await http_request.is_disconnected():
                return

            search_start = time.time()
            search_results = self.vector_store.search_similar(query, k)
            filtered_results, original_count = filter_search_results(search_results)
            search_end = time.time()
            search_ms = (search_end - search_start) * 1000

            if not filtered_results:
                yield sse_error(
                    "retrieval",
                    "No relevant information found in stored chunks",
                )
                return

            search_results = filtered_results
            distances = [r.get("similarity_score", 0) for r in search_results]
            confidence_score, confidence_label = compute_retrieval_confidence(distances)
            avg_distance = sum(distances) / len(distances) if distances else 0.0

            yield format_sse(
                "retrieval_completed",
                {
                    "chunks": search_results,
                    "count": len(search_results),
                    "filtered_count": original_count - len(search_results),
                    "original_count": original_count,
                    "latency_ms": round(search_ms, 2),
                    "avg_distance": round(avg_distance, 4),
                    "retrieval_confidence": confidence_label,
                    "confidence_score": confidence_score,
                    "threshold": SIMILARITY_THRESHOLD,
                    "timestamp": utc_timestamp(),
                },
            )

            if await http_request.is_disconnected():
                return

            yield format_sse(
                "generation_started",
                {
                    "model": "google/flan-t5-base",
                    "context_chunks": len(search_results),
                    "timestamp": utc_timestamp(),
                },
            )

            llm_start = time.time()
            for token_text in self.llm_service.generate_response_stream(
                query, search_results, max_length
            ):
                if await http_request.is_disconnected():
                    return

                full_response += token_text
                yield format_sse("token", {"text": token_text})

            llm_end = time.time()
            llm_ms = (llm_end - llm_start) * 1000

            if await http_request.is_disconnected():
                return

            context_texts = [r.get("chunk_text", "") for r in search_results]
            hallucination_metrics = self._evaluator.detect_hallucination(
                full_response, context_texts
            )

            yield format_sse(
                "evaluation_complete",
                {
                    "grounding_score": hallucination_metrics["grounding_score"],
                    "hallucination_detected": hallucination_metrics["hallucination_detected"],
                    "confidence_label": confidence_label,
                    "confidence_score": confidence_score,
                    "grounded_phrases": hallucination_metrics["grounded_phrases"],
                    "total_phrases": hallucination_metrics["total_phrases"],
                    "timestamp": utc_timestamp(),
                },
            )

            total_ms = (time.time() - pipeline_start) * 1000
            embedding_ms = search_ms  # search includes query embedding

            observability.track_rag_pipeline(
                query=query,
                total_latency_ms=total_ms,
                embedding_time_ms=embedding_ms,
                search_time_ms=search_ms,
                llm_time_ms=llm_ms,
                success=True,
                operation_id=f"stream_{int(pipeline_start * 1000)}",
                k=k,
                response_length=len(full_response),
                tokens_used=len(full_response.split()),
                distances=distances,
                response_text=full_response,
            )

            yield format_sse(
                "completed",
                {
                    "query": query,
                    "response": full_response,
                    "context_used": len(search_results),
                    "total_latency_ms": round(total_ms, 2),
                    "embedding_ms": round(embedding_ms, 2),
                    "search_ms": round(search_ms, 2),
                    "llm_ms": round(llm_ms, 2),
                    "tokens_used": len(full_response.split()),
                    "model_info": {
                        "model": "google/flan-t5-base",
                        "parameters": "770M",
                        "type": "text-to-text-generation",
                    },
                    "retrieved_chunks": search_results,
                    "timestamp": utc_timestamp(),
                },
            )

        except Exception as e:
            yield sse_error("generation", str(e))
