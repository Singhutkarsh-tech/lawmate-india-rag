from __future__ import annotations

from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder

_cross_encoder: Optional[CrossEncoder] = None
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # can swap 


def get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
    return _cross_encoder


def rerank_chunks(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    
    if not candidates:
        return []

    model = get_cross_encoder()

    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)  # array of floats

    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)

    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    return candidates[:top_k]


if __name__ == "__main__":
    from src.retrieval.hybrid_retriever import search_similar_chunks  # adjust name if needed

    q = "powers and jurisdiction of the Delhi Special Police Establishment"
    initial = search_similar_chunks(q, top_k=15)
    print(f"Initial retrieved: {len(initial)}")

    reranked = rerank_chunks(q, initial, top_k=5)
    print(f"Reranked top: {len(reranked)}")

    for i, c in enumerate(reranked, start=1):
        print(f"\n=== Reranked {i} (score={c['rerank_score']:.4f}) ===")
        print("Section:", c["section_id"], "-", c["section_heading"])
        print("Pages  :", c["page_start"], "→", c["page_end"])
        print("Preview:", c["text"][:300], "...")