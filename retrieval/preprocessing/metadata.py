import datetime

class MetadataEnricher:
    """Attaches document origin, line counts, and hashes to parsed content."""
    
    @staticmethod
    def enrich(text: str, source_metadata: dict) -> dict:
        import hashlib
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        
        enriched = {
            "checksum": checksum,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "word_count": len(text.split())
        }
        enriched.update(source_metadata)
        return enriched
