import json
from pathlib import Path

import pytest

from copilot.services import ask_data
from copilot.services.sql_guard import SqlGuardError
from tests.support import make_fake

_CASES = json.loads((Path(__file__).resolve().parent / "fixtures" / "eval_cases.json").read_text())


@pytest.mark.parametrize("case", _CASES, ids=[case["name"] for case in _CASES])
def test_eval_case(case, acme):
    fake = make_fake()
    if case["blocked"]:
        with pytest.raises(SqlGuardError):
            ask_data.prepare_ask(acme, case["question"], llm=fake)
        return

    prep = ask_data.prepare_ask(acme, case["question"], llm=fake)
    if "sql_contains" in case:
        assert case["sql_contains"] in prep["sql"].lower()
    if "pii" in case:
        assert all(case["pii"] not in call for call in fake.calls)
        assert any("[EMAIL]" in call for call in fake.calls)
