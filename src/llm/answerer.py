from __future__ import annotations
from typing import Any, List, Optional, Sequence
from pydantic import BaseModel
import ollama


class SectionCitation(BaseModel):
    doc_id: str
    section_id: Optional[str]
    heading: Optional[str]
    page_start: int
    page_end: int


class LLMAnswer(BaseModel):
    answer: str
    citations: List[SectionCitation]


def _get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _chunk_to_citation(chunk: Any) -> SectionCitation:
    return SectionCitation(
        doc_id=str(_get(chunk, "doc_id", "")),
        section_id=_get(chunk, "section_id", None),
        heading=_get(chunk, "section_heading", None),
        page_start=int(_get(chunk, "page_start", 0)),
        page_end=int(_get(chunk, "page_end", 0)),
    )


def build_context_block(chunks: Sequence[Any]) -> str:
    lines: List[str] = []
    for i, ch in enumerate(chunks, start=1):
        doc_id = _get(ch, "doc_id", "")
        section_id = _get(ch, "section_id", None)
        heading = _get(ch, "section_heading", None)
        page_start = _get(ch, "page_start", None)
        page_end = _get(ch, "page_end", None)
        text = _get(ch, "text", "")
        title_bits: List[str] = []
        if section_id:
            title_bits.append(f"Section {section_id}")
        if heading:
            title_bits.append(heading)
        title = " – ".join(title_bits) if title_bits else "(unnamed section)"
        page_info = ""
        if page_start is not None and page_end is not None:
            page_info = f" (pages {page_start}–{page_end})"
        lines.append(f"[Context {i}] {title}{page_info} [Doc: {doc_id}]")
        lines.append(text.strip())
        lines.append("")
    return "\n".join(lines).strip()


def build_prompt(query: str, chunks: Sequence[Any]) -> str:
    context_block = build_context_block(chunks)
    return f"""
    You are LawMate, a careful Indian legal assistant. You answer questions only using the
context passages from statutes and acts that I give you.

Rules:
- Use ONLY the information in the provided context.
- If the answer is unclear or not present in the context, say so clearly.
- Quote or paraphrase the relevant sections and mention their section numbers.
- Be concise but precise. Prefer clear bullet points over long paragraphs.
- Never invent new laws or sections that are not in the context.

User question:
{query}

Relevant legal context:
-----------------------
{context_block}
-----------------------

Now, based ONLY on the above context, provide your answer.
If the context does not contain enough information, say:
"I cannot answer this confidently from the provided sections."
""".strip()


def call_llama(prompt: str, model: str = "llama3.2:3b") -> str:
    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise Indian legal assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp["message"]["content"].strip()


def answer_with_llm(query: str, chunks: Sequence[Any], model: str = "llama3.2:3b") -> LLMAnswer:
    if not chunks:
        text = "I could not retrieve any relevant statutory text to answer this question from the index."
        return LLMAnswer(answer=text, citations=[])
    prompt = build_prompt(query, chunks)
    answer_text = call_llama(prompt, model=model)
    citations_map: dict[tuple, SectionCitation] = {}
    for ch in chunks:
        cit = _chunk_to_citation(ch)
        key = (cit.doc_id, cit.section_id, cit.page_start, cit.page_end)
        citations_map[key] = cit
    return LLMAnswer(answer=answer_text, citations=list(citations_map.values()))