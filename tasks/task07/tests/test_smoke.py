from __future__ import annotations

from unionlab.schemas import CompactTicket, DetailedTicket, build_union_validator, validate_payload


def test_local_helper_validates_compact_payload(compact_ticket_payload):
    result = validate_payload(compact_ticket_payload)
    assert isinstance(result, CompactTicket)
    assert result.x == 1


def test_local_helper_validates_detailed_payload(full_ticket_payload):
    result = validate_payload(full_ticket_payload, order="detailed_first")
    assert isinstance(result, DetailedTicket)
    assert result.x == 1
    assert result.y == 2


def test_union_validator_builder_accepts_explicit_mode(compact_ticket_payload):
    validator = build_union_validator(mode="left_to_right")
    result = validator.validate_python(compact_ticket_payload)
    assert isinstance(result, CompactTicket)
