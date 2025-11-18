from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.retrieval.hybrid_retriever import search_similar_chunks
from src.retrieval.ranker import rerank_chunks
from src.llm.answerer import answer_with_llm, LLMAnswer


app = FastAPI(
    title="LawMate India RAG API",
    version="0.1.0",
)


class AskRequest(BaseModel):
    question: str
    top_k: int = 20
    rerank_k: int = 5


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=LLMAnswer)
def ask(payload: AskRequest) -> LLMAnswer:
    q = payload.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="question cannot be empty")

    initial = search_similar_chunks(q, top_k=payload.top_k)
    if not initial:
        return LLMAnswer(
            answer="I could not retrieve any relevant statutory text to answer this question from the index.",
            citations=[],
        )

    reranked = rerank_chunks(q, initial, top_k=payload.rerank_k)
    resp = answer_with_llm(q, reranked)
    return resp