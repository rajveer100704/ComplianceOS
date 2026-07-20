import json
from sqlalchemy import ForeignKey, String, TEXT, JSON, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin

# Custom type decorator fallback to handle pgvector column types on SQLite gracefully
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    class Vector(TypeDecorator):
        """Fallback type decorator to map vector arrays as JSON strings on SQLite."""
        impl = TEXT
        cache_ok = True
        
        def process_bind_param(self, value, dialect):
            if value is not None:
                return json.dumps(value)
            return value
            
        def process_result_value(self, value, dialect):
            if value is not None:
                return json.loads(value)
            return value

class ChunkModel(Base, AuditMixin):
    """Maps document text chunks with their dense vector embeddings and metadata."""
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    embedding = mapped_column(Vector(512), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    document = relationship("DocumentModel")
