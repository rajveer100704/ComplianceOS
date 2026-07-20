from typing import List
from retrieval.base import BaseChunker
from retrieval.models.chunk import Chunk
from retrieval.registry import register_chunker

@register_chunker("paragraph")
class ParagraphChunker(BaseChunker):
    """Splits raw text into paragraph blocks based on double newlines."""

    def chunk(self, doc_id: int, text: str, doc_metadata: dict) -> List[Chunk]:
        paragraphs = text.split("\n\n")
        chunks = []
        for i, p in enumerate(paragraphs):
            p_text = p.strip()
            if p_text:
                cid = f"doc_{doc_id}_p_{i}"
                meta = doc_metadata.copy()
                meta.update({"page": 1, "paragraph_index": i})
                chunks.append(Chunk(chunk_id=cid, document_id=doc_id, text=p_text, metadata=meta))
        return chunks
