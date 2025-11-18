from src.retrieval.hybrid_retriever import search_similar_chunks
from src.retrieval.ranker import rerank_chunks
from src.llm.answerer import answer_with_llm

q = "What powers does the Delhi Special Police Establishment have in States?"
initial = search_similar_chunks(q, top_k=20)
reranked = rerank_chunks(q, initial, top_k=5)
resp = answer_with_llm(q, reranked)
print(resp.answer)
print(resp.citations)