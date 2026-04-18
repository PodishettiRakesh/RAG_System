import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from contextlib import contextmanager


class ObservabilityTracker:
    """Comprehensive observability and tracking system for RAG operations."""
    
    def __init__(self):
        # Configure structured logging
        self.logger = logging.getLogger("RAG_System")
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with structured formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Global metrics storage
        self.metrics = {
            "requests": [],
            "embeddings": [],
            "vector_search": [],
            "vector_search_start": [],
            "vector_search_complete": [],
            "llm_generation": [],
            "llm_generation_start": [],
            "llm_generation_complete": [],
            "rag_pipeline": []
        }
    
    def log_structured(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """Log structured event with timestamp."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "level": level,
            **data
        }
        
        # Log as JSON for structured parsing
        self.logger.info(json.dumps(log_entry, default=str))
        
        # Store in metrics
        if event_type in self.metrics:
            self.metrics[event_type].append(log_entry)
            # print(f"🔍 DEBUG: Stored {event_type} event. Total {event_type} events: {len(self.metrics[event_type])}")
        else:
            print(f"⚠️ DEBUG: Unknown event_type: {event_type}")
    
    @contextmanager
    def track_latency(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to track operation latency."""
        start_time = time.time()
        operation_id = f"{operation}_{int(start_time * 1000)}"
        
        # Log operation start
        # self.log_structured(f"{operation}_start", {
        #     "operation_id": operation_id,
        #     "metadata": metadata or {}
        # })
        
        try:
            yield operation_id
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # Calculate and log latency
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            self.log_structured(f"{operation}_complete", {
                "operation_id": operation_id,
                "latency_ms": round(latency_ms, 2),
                "success": success,
                "error": error,
                "metadata": metadata or {}
            })
    
    def track_embedding_generation(self, chunks_count: int, dimensions: int, operation_id: str):
        """Track embedding generation metrics."""
        self.log_structured("embedding_generation", {
            "operation_id": operation_id,
            "chunks_count": chunks_count,
            "dimensions": dimensions,
            "total_vectors": chunks_count * dimensions
        })
    
    def track_vector_search(self, query_length: int, k: int, results_count: int, operation_id: str):
        """Track vector search metrics."""
        # self.log_structured("vector_search", {
        #     "operation_id": operation_id,
        #     "query_length": query_length,
        #     "k_requested": k,
        #     "results_count": results_count,
        #     "success_rate": results_count / k if k > 0 else 0
        # })
    
    def track_llm_generation(self, query_length: int, context_chunks: int, 
                           response_length: int, tokens_used: int, operation_id: str):
        """Track LLM generation metrics."""
        # self.log_structured("llm_generation", {
        #     "operation_id": operation_id,
        #     "query_length": query_length,
        #     "context_chunks": context_chunks,
        #     "response_length": response_length,
        #     "tokens_used": tokens_used,
        #     "tokens_per_second": tokens_used / 0.1 if operation_id else 0  # Approximate
        # })
    
    def track_rag_pipeline(self, query: str, total_latency_ms: float, 
                          embedding_time_ms: float, search_time_ms: float, 
                          llm_time_ms: float, success: bool, operation_id: str,
                          k: int = 3, response_length: int = 0, tokens_used: int = 0,
                          distances: list = None, response_text: str = ""):
        """Track complete RAG pipeline metrics."""
        print(f"🔍 DEBUG: track_rag_pipeline called with query: {query[:50]}...")
        
        # Calculate performance breakdown
        embedding_pct = round((embedding_time_ms / total_latency_ms) * 100, 1)
        search_pct = round((search_time_ms / total_latency_ms) * 100, 1)
        llm_pct = round((llm_time_ms / total_latency_ms) * 100, 1)
        
        # Detect bottleneck
        if llm_time_ms > search_time_ms and llm_time_ms > embedding_time_ms:
            bottleneck = "LLM"
        elif search_time_ms > embedding_time_ms:
            bottleneck = "Search"
        else:
            bottleneck = "Embedding"
        
        # Store structured metrics
        print(f"🔍 DEBUG: Storing rag_pipeline event...")
        self.log_structured("rag_pipeline", {
            "operation_id": operation_id,
            "query": query,
            "k": k,
            "query_length": len(query),
            "total_latency_ms": round(total_latency_ms, 2),
            "embedding_time_ms": round(embedding_time_ms, 2),
            "search_time_ms": round(search_time_ms, 2),
            "llm_time_ms": round(llm_time_ms, 2),
            "success": success,
            "response_length": response_length,
            "tokens_used": tokens_used,
            "retrieved_chunks": len(distances) if distances else 0,
            "distances": distances or [],
            "performance_breakdown": {
                "embedding_percentage": embedding_pct,
                "search_percentage": search_pct,
                "llm_percentage": llm_pct
            },
            "bottleneck": bottleneck,
            "response_text": response_text
        })
        
        # Print clean summary
        self.print_rag_pipeline_summary(
            query=query,
            k=k,
            retrieved_chunks=len(distances) if distances else 0,
            distances=distances or [],
            response_length=response_length,
            tokens_used=tokens_used,
            embedding_time_ms=round(embedding_time_ms, 2),
            search_time_ms=round(search_time_ms, 2),
            llm_time_ms=round(llm_time_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
            embedding_pct=embedding_pct,
            search_pct=search_pct,
            llm_pct=llm_pct,
            bottleneck=bottleneck,
            response_text=response_text
        )
    
    def print_rag_pipeline_summary(self, query: str, k: int, retrieved_chunks: int, 
                          response_length: int, tokens_used: int, distances: list,
                          embedding_time_ms: float, search_time_ms: float, 
                          llm_time_ms: float, total_latency_ms: float,
                          embedding_pct: float, search_pct: float, llm_pct: float,
                          bottleneck: str, response_text: str = ""):
        """Print clean, human-readable RAG pipeline summary."""
        print(f"\n{'-'*60}")
        print(f"{'-'*20} RAG PIPELINE SUMMARY {'-'*20}")
        print(f"{'-'*60}")
        print(f"Query: \"{query}\"")
        print(f"Top-K: {k}")
        
        # Add Response section if response text is provided
        if response_text:
            print(f"\n{'-'*25} Response {'-'*25}")
            preview = response_text[:75] + "..." if len(response_text) > 50 else response_text
            print(f"- Answer (preview): {preview}")
            print(f"- Length: {response_length} chars")
        
        print(f"\n{'-'*25} Retrieval {'-'*25}")
        print(f"- Chunks Retrieved: {retrieved_chunks}")
        if distances:
            print(f"- Distances: [{', '.join([f'{d:.2f}' for d in distances[:3]])}{'...' if len(distances) > 3 else ''}]")
        print(f"\n{'-'*25} LLM {'-'*25}")
        print(f"- Response Length: {response_length} chars")
        print(f"- Tokens Used: {tokens_used}")
        print(f"\n{'-'*25} Latency Breakdown {'-'*25}")
        print(f"- Embedding: {embedding_time_ms} ms ({embedding_pct}%)")
        print(f"- Retrieval: {search_time_ms} ms ({search_pct}%)")
        print(f"- LLM: {llm_time_ms} ms ({llm_pct}%)")
        print(f"- Total: {total_latency_ms} ms")
        print(f"\n{'-'*25} Performance Insight {'-'*25}")
        print(f"- Bottleneck: {bottleneck} ({max(embedding_pct, search_pct, llm_pct)}% time)")
        avg_distance = sum(distances) / len(distances) if distances else 0

        if avg_distance < 1.0:
            quality = "High"
            distance_info = ""
        elif avg_distance < 1.5:
            quality = "Moderate"
            distance_info = " (distance > 1.0 for some chunks)"
        else:
            quality = "Low"
            distance_info = " (poor semantic match)"
            
        print(f"- Retrieval Quality: {quality} (avg distance: {avg_distance:.2f}){distance_info}")
        print(f"{'-'*60}\n")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked metrics."""
        summary = {}
        
        for event_type, events in self.metrics.items():
            if events:
                summary[event_type] = {
                    "total_events": len(events),
                    "last_event": events[-1]["timestamp"] if events else None
                }
                
                # Calculate latencies if available
                latencies = [event.get("latency_ms", 0) for event in events if "latency_ms" in event]
                if latencies:
                    summary[event_type]["latency_stats"] = {
                        "avg_ms": round(sum(latencies) / len(latencies), 2),
                        "min_ms": round(min(latencies), 2),
                        "max_ms": round(max(latencies), 2)
                    }
        
        # Add RAG pipeline specific stats
        if "rag_pipeline" in self.metrics and self.metrics["rag_pipeline"]:
            rag_events = self.metrics["rag_pipeline"]
            total_queries = len(rag_events)
            avg_latency = sum(e.get("total_latency_ms", 0) for e in rag_events) / total_queries
            avg_llm_time = sum(e.get("llm_time_ms", 0) for e in rag_events) / total_queries
            
            summary["rag_pipeline"]["summary"] = {
                "total_queries": total_queries,
                "avg_latency_ms": round(avg_latency, 2),
                "avg_llm_time_ms": round(avg_llm_time, 2),
                "success_rate": sum(1 for e in rag_events if e.get("success", False)) / total_queries * 100
            }
        
        return summary
    
    

# Global observability instance
observability = ObservabilityTracker()


def track_operation(operation_type: str, include_metadata: bool = False):
    """Decorator to automatically track function operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metadata = None
            if include_metadata:
                metadata = {
                    "function": func.__name__
                }
            
            with observability.track_latency(operation_type, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class PerformanceTracker:
    """Helper class for tracking RAG pipeline performance."""
    
    def __init__(self, operation_id: str):
        self.operation_id = operation_id
        self.start_time = time.time()
        self.timings = {}
    
    def mark_step(self, step_name: str):
        """Mark a step in the pipeline."""
        current_time = time.time()
        self.timings[step_name] = {
            "timestamp": current_time,
            "elapsed_ms": (current_time - self.start_time) * 1000
        }
    
    def get_step_latency(self, step_name: str) -> float:
        """Get latency for a specific step."""
        if step_name in self.timings:
            return self.timings[step_name]["elapsed_ms"]
        return 0.0
    
    def get_total_latency(self) -> float:
        """Get total pipeline latency."""
        return (time.time() - self.start_time) * 1000
