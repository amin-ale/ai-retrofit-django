from copilot.services.redaction import redact, redact_rows


def test_redacts_email():
    assert redact("write to jane.doe@example.com now") == "write to [EMAIL] now"


def test_redacts_card_and_ssn_and_phone():
    assert "[CARD]" in redact("card 4111 1111 1111 1111")
    assert "[SSN]" in redact("ssn 123-45-6789")
    assert "[PHONE]" in redact("call (415) 555-0132")


def test_redact_rows_only_touches_strings():
    rows = [["mail me at a@b.com", 5], ["clean", 9]]
    assert redact_rows(rows) == [["mail me at [EMAIL]", 5], ["clean", 9]]
