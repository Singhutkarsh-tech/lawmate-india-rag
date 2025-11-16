from __future__ import annotations

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from pymilvus import Collection

from src.pipelines.embedder import get_model 
from src.pipelines.indexer import get_or_create_collection



def embed_query(text: str) -> List[float]:
    model: SentenceTransformer = get_model()
    emb = model.encode([text]) 
    return emb[0].tolist()


def search_similar_chunks(
    query: str,
    top_k: int = 10,
    ) -> List[Dict[str, Any]]:
    
    coll: Collection = get_or_create_collection()

    q_emb = embed_query(query)

    search_params = {
        "metric_type": "COSINE",    
        "params": {"nprobe": 10},
    }

    results = coll.search(
        data=[q_emb],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=[
            "chunk_id",
            "doc_id",
            "section_id",
            "section_heading",
            "part",
            "chapter",
            "page_start",
            "page_end",
            "text",
        ],
    )

    hits = results[0]  # we passed a single query vector
    out: List[Dict[str, Any]] = []

    for hit in hits:
        entity = hit.entity
        out.append(
            {
                "chunk_id": entity.get("chunk_id"),
                "doc_id": entity.get("doc_id"),
                "section_id": entity.get("section_id"),
                "section_heading": entity.get("section_heading"),
                "part": entity.get("part"),
                "chapter": entity.get("chapter"),
                "page_start": entity.get("page_start"),
                "page_end": entity.get("page_end"),
                "text": entity.get("text"),
                "score": float(hit.distance),
            }
        )

    return out


if __name__ == "__main__":
    q = "What are the powers and jurisdiction of the Delhi Special Police Establishment"
    chunks = search_similar_chunks(q, top_k=5)
    print(f"Got {len(chunks)} hits")
    for i, c in enumerate(chunks, start=1):
        print(f"\n--- Hit {i} (score={c['score']:.4f}) ---")
        print("Doc ID   :", c["doc_id"])
        print("Section  :", c["section_id"], "-", c["section_heading"])
        print("Pages    :", c["page_start"], "→", c["page_end"])
        print("Preview  :", c["text"][:400], "...")