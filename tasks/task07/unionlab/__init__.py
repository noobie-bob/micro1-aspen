"""Local pydantic-core union-selection benchmark substrate."""
from .schemas import build_union_validator, validate_payload

__all__ = ["build_union_validator", "validate_payload"]
