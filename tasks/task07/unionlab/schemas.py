from __future__ import annotations

from typing import Any
from pydantic_core import SchemaValidator, core_schema


class CompactTicket:
    """Model-like class with one visible field."""

    def __init__(self, x: int, **extra: Any) -> None:
        self.x = x
        for key, value in extra.items():
            setattr(self, key, value)


class DetailedTicket(CompactTicket):
    """More-specific model-like class with an additional field."""

    def __init__(self, x: int, y: int, **extra: Any) -> None:
        super().__init__(x=x, y=y, **extra)


class ArchiveTicket(CompactTicket):
    """Third variant used by smoke tests to show normal validation works."""

    def __init__(self, x: int, archived: bool, **extra: Any) -> None:
        super().__init__(x=x, archived=archived, **extra)


def _model_schema(cls: type[Any], fields: dict[str, Any]) -> core_schema.CoreSchema:
    return core_schema.model_schema(
        cls,
        core_schema.model_fields_schema(
            {
                name: core_schema.model_field(schema)
                for name, schema in fields.items()
            }
        ),
    )


def compact_ticket_schema() -> core_schema.CoreSchema:
    return _model_schema(CompactTicket, {"x": core_schema.int_schema()})


def detailed_ticket_schema() -> core_schema.CoreSchema:
    return _model_schema(
        DetailedTicket,
        {"x": core_schema.int_schema(), "y": core_schema.int_schema()},
    )


def archive_ticket_schema() -> core_schema.CoreSchema:
    return _model_schema(
        ArchiveTicket,
        {"x": core_schema.int_schema(), "archived": core_schema.bool_schema()},
    )


def build_union_validator(order: str = "compact_first", mode: str | None = None) -> SchemaValidator:
    """Build a small pydantic-core union validator for smoke tests.

    Parameters
    ----------
    order:
        ``compact_first`` creates Union[CompactTicket, DetailedTicket].
        ``detailed_first`` creates Union[DetailedTicket, CompactTicket].
        ``three_way`` places the best match in the middle.
    mode:
        Optional pydantic-core union mode, such as ``smart`` or ``left_to_right``.
    """
    if order == "compact_first":
        choices = [compact_ticket_schema(), detailed_ticket_schema()]
    elif order == "detailed_first":
        choices = [detailed_ticket_schema(), compact_ticket_schema()]
    elif order == "three_way":
        choices = [compact_ticket_schema(), detailed_ticket_schema(), archive_ticket_schema()]
    else:
        raise ValueError(f"unknown order: {order}")

    kwargs: dict[str, Any] = {}
    if mode is not None:
        kwargs["mode"] = mode
    return SchemaValidator(core_schema.union_schema(choices, **kwargs))


def validate_payload(payload: dict[str, Any], *, order: str = "compact_first", mode: str | None = None) -> Any:
    """Validate a payload using the local union helper."""
    return build_union_validator(order=order, mode=mode).validate_python(payload)
