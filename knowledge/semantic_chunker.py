from __future__ import annotations

from knowledge.chunker import KnowledgeChunk, KnowledgeTrace, chunk_text

__all__ = ["KnowledgeChunk", "KnowledgeTrace", "chunk_text", "semantic_chunk_text"]


def semantic_chunk_text(
    text: str,
    source_file: str,
    page: int = 0,
    max_chars: int = 900,
) -> list[KnowledgeChunk]:
    return chunk_text(text=text, source_file=source_file, page=page, max_chars=max_chars)
