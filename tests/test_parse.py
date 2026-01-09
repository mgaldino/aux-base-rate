from base_rate_harness.parse import extract_rationale, parse_base_rate


def test_parse_base_rate_accepts_percent_and_bounds() -> None:
    for text in [
        "BASE_RATE: 0%\nRATIONALE: ok",
        "base_rate: 50\nRATIONALE: ok",
        "  Base_Rate: 100 %\nRATIONALE: ok",
    ]:
        value, err = parse_base_rate(text)
        assert err is None
        assert value is not None


def test_parse_base_rate_rejects_out_of_bounds() -> None:
    for text in [
        "BASE_RATE: 101%\nRATIONALE: nope",
        "BASE_RATE: 999\nRATIONALE: nope",
        "BASE_RATE: -1%\nRATIONALE: nope",
    ]:
        value, err = parse_base_rate(text)
        assert value is None
        assert err == "out_of_bounds"


def test_extract_rationale_after_marker() -> None:
    text = "BASE_RATE: 12%\nRATIONALE: Because of reasons."
    assert extract_rationale(text) == "Because of reasons."
