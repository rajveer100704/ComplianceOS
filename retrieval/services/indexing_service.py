from retrieval.base import BaseChunker, BaseEmbeddingProvider, BaseVectorStore
from retrieval.indexing.builder import IndexBuilder
from retrieval.preprocessing.normalizer import TextNormalizer
from retrieval.preprocessing.cleaner import TextCleaner
from retrieval.preprocessing.metadata import MetadataEnricher
from retrieval.models.document_graph import DocumentGraph
from retrieval.models.chunk import DocumentNode

class IndexingService:
    """Orchestrates text cleaning, metadata enrichment, chunking, and database upserts."""

    def __init__(self, chunker: BaseChunker, embedding_provider: BaseEmbeddingProvider, vector_store: BaseVectorStore, cache = None):
        self.chunker = chunker
        self.builder = IndexBuilder(embedding_provider, vector_store, cache=cache)

    def index_document(self, doc_id: int, filename: str, raw_text: str, custom_metadata: dict = None) -> DocumentGraph:
        # Preprocessing
        normalized = TextNormalizer.normalize(raw_text)
        cleaned = TextCleaner.clean(normalized)
        
        # Metadata Enrichment
        base_meta = {"filename": filename, "document_id": doc_id}
        if custom_metadata:
            base_meta.update(custom_metadata)
        meta = MetadataEnricher.enrich(cleaned, base_meta)
        
        # Chunker
        chunks = self.chunker.chunk(doc_id, cleaned, meta)
        
        # Build vector indexes
        self.builder.build_index(chunks)
        
        # Build logical graph
        graph = DocumentGraph()
        graph.documents[doc_id] = DocumentNode(document_id=doc_id, filename=filename, metadata=meta)
        for c in chunks:
            graph.chunks[c.chunk_id] = c
            
        return graph
