from datetime import datetime
from typing import Any, Optional


def validate_metadata(metadata: dict[str, Any], schema: Optional[dict] = None) -> dict[str, Any]:
    """Validate and clean metadata values. Ensures all values are storable types."""
    clean = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, list):
            # Convert list to comma-separated string for storage
            clean[key] = ",".join(str(v) for v in value)
        elif isinstance(value, datetime):
            clean[key] = value.isoformat()
        elif isinstance(value, dict):
            # Flatten nested dicts with dot notation
            for sub_key, sub_val in value.items():
                clean[f"{key}.{sub_key}"] = str(sub_val)
        else:
            clean[key] = str(value)

    return clean


def enrich_metadata(metadata: dict[str, Any], text: str, source: str = "api") -> dict[str, Any]:
    """Add computed metadata fields to a document."""
    enriched = {**metadata}
    enriched["_source"] = source
    enriched["_ingested_at"] = datetime.utcnow().isoformat()
    enriched["_char_count"] = len(text)
    enriched["_word_count"] = len(text.split())
    enriched["_token_estimate"] = len(text) // 4
    return enriched
