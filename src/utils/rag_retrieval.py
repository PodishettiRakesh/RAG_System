"""Shared retrieval filtering utilities for RAG endpoints."""

from typing import Dict, List, Tuple

SIMILARITY_THRESHOLD = 1.5


def filter_search_results(
    search_results: List[Dict], threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[List[Dict], int]:
    """
    Filter chunks by L2 distance threshold (lower is better).

    Returns:
        Tuple of (filtered_results, original_count)
    """
    original_count = len(search_results)
    filtered = [
        result
        for result in search_results
        if result.get("similarity_score", float("inf")) <= threshold
    ]
    return filtered, original_count


def compute_retrieval_confidence(distances: List[float]) -> Tuple[float, str]:
    """Compute confidence score and label from retrieval distances."""
    if not distances:
        return 0.0, "LOW"
    avg_distance = sum(distances) / len(distances)
    confidence_score = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))
    if confidence_score > 0.7:
        label = "HIGH"
    elif confidence_score > 0.4:
        label = "MEDIUM"
    else:
        label = "LOW"
    return round(confidence_score, 3), label
