"""API routes package."""

from beanie import PydanticObjectId
from beanie.odm.fields import Link


def get_link_id(link_or_doc) -> str:
    """Extract ID from a Beanie Link or Document object.

    When a document is created with a reference, the field holds the actual
    document. When fetched from DB without fetch_links, it's a Link with .ref.id.
    """
    # If it's a Link object (not fetched), use ref.id
    if isinstance(link_or_doc, Link):
        return str(link_or_doc.ref.id)
    # If it's a Document with an id attribute
    if hasattr(link_or_doc, "id"):
        return str(link_or_doc.id)
    # Fallback: try ref.id
    if hasattr(link_or_doc, "ref") and hasattr(link_or_doc.ref, "id"):
        return str(link_or_doc.ref.id)
    raise ValueError(f"Cannot extract ID from {type(link_or_doc)}")


def check_link_id(link_or_doc, expected_id: PydanticObjectId) -> bool:
    """Check if a Link or Document matches an expected ID."""
    return PydanticObjectId(get_link_id(link_or_doc)) == expected_id
