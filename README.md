# LawMate India – Legal RAG System

LawMate India is a fully custom Retrieval-Augmented Generation (RAG) system built to answer Indian legal questions grounded strictly in statutory text.  
The project handles the complete pipeline end-to-end: document ingestion, parsing, intelligent chunking, embedding, hybrid search, reranking, and LLM-based answers with citations.

---

## Features

### Document Processing
- PDF extraction and cleaning  
- Legal-aware sectionization (Section 1, 2(1A), 4B, etc.)  
- Sentence-aware, overlap-aware chunking  

### Retrieval Pipeline
- Milvus vector database (FAISS-style ANN search)  
- BM25 keyword retrieval  
- Hybrid ranking: vector + sparse search  
- Cross-encoder (BERT) reranking  

### Answer Generation
- Local Llama model through Ollama  
- Context-grounded answers only  
- Automatic section citations  
- No hallucinations — declines if context insufficient  

### API
FastAPI endpoint that performs:  
1. Hybrid retrieval  
2. Cross-encoder reranking  
3. Prompt construction  
4. LLM answer  
5. Citations return as JSON

Endpoint:
POST /ask
body: { “query”: “Your legal question” }


## Project Structure
src/
├── parsing/             # extract & clean text
├── pipelines/           # sectionizer, chunker, embedder, indexer
├── retrieval/           # hybrid search + BERT cross-encoder
├── llm/                 # Llama-based answerer
└── api/                 # FastAPI app

---

## Tech Stack

- **Python 3.13**
- **Milvus** for vector indexing
- **SentenceTransformers** for embeddings
- **BM25** (rank-bm25) for sparse search
- **BERT Cross-Encoder** for reranking
- **Llama 3 (via Ollama)** for answer generation
- **FastAPI** for serving

---

## How It Works (End-to-End)

1. **Parse** PDFs into cleaned pages  
2. **Sectionize** using legal regex patterns  
3. **Chunk** into overlapping, semantic units  
4. **Embed** chunks into vectors  
5. **Index** into Milvus  
6. **Retrieve** using hybrid search  
7. **Rerank** using BERT cross-encoder  
8. **Generate** a grounded answer using Llama  
9. **Return** answer + citations  

---

## Running the System

Index all parsed legal acts:
python -m src.pipelines.indexer

Test the retriever:
python -m src.retrieval.hybrid_retriever

Test the answerer:
python -m src.llm.check_answerer

Start the API:
uvicorn src.api.main:app –reload

---

## Example Query
POST /ask
{
“query”: “What powers does the Delhi Special Police Establishment have in States?”
}

Example Output:
{
“answer”: “The DSPE may exercise powers in a State under Sections 5 and 6A…”,
“citations”: [
{ “doc_id”: “…”, “section_id”: “5”, “page_start”: 3, “page_end”: 4 }
]
}

---

## Status
✔️ MVP completed  
✔️ End-to-end working  
✔️ Ready for scaling to multiple Acts  
✔️ Perfect for resume + interviews

---

## Author
Built by **Utkarsh Singh** as a practical deep-dive into real-world RAG systems, legal text processing, and hybrid retrieval architectures.


LawMate India is an open, evolving project.
If you’re interested in legal NLP, RAG systems, document intelligence, or improving access to Indian statutory law, collaborations are warmly invited.

Feel free to open issues, submit PRs, or reach out directly.
