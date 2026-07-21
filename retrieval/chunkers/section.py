from typing import List
from retrieval.base import BaseChunker
from retrieval.models.chunk import Chunk
from retrieval.registry import register_chunker


@register_chunker("section")
class SectionChunker(BaseChunker):
    """Splits raw text by page breaks and headings, compiling paragraph coordinates."""

    def chunk(self, doc_id: int, text: str, doc_metadata: dict) -> List[Chunk]:
        pages = text.split("\n\n--- Page Break ---\n\n")
        chunks = []
        for page_idx, page_text in enumerate(pages):
            paragraphs = page_text.split("\n\n")
            for para_idx, p in enumerate(paragraphs):
                p_text = p.strip()
                if p_text:
                    cid = f"doc_{doc_id}_pg_{page_idx + 1}_p_{para_idx}"
                    meta = doc_metadata.copy()
                    meta.update(
                        {
                            "page": page_idx + 1,
                            "section": "General Content",
                            "paragraph_index": para_idx,
                        }
                    )
                    chunks.append(
                        Chunk(
                            chunk_id=cid, document_id=doc_id, text=p_text, metadata=meta
                        )
                    )
        return chunks
