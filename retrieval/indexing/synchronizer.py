from retrieval.models.document_graph import DocumentGraph


class IndexSynchronizer:
    """Synchronizes logical DocumentGraph states with physical vector stores."""

    def __init__(self, builder):
        self.builder = builder

    def sync(self, graph: DocumentGraph) -> None:
        """Pushes chunks collected in the document graph to the builder."""
        chunks = list(graph.chunks.values())
        self.builder.incremental_update(chunks)
