"""Intent enumeration for classification."""

from enum import Enum


class IntentType(str, Enum):
    """Intent classification types."""

    TRIVIAL = "TRIVIAL"
    FAQ = "FAQ"
    CONSULTANT = "CONSULTANT"
    OTHER = "OTHER"
