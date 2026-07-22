import json
from pathlib import Path

from copilot.llm.fake_client import FakeLLMClient

_DEMO = Path(__file__).resolve().parent.parent / "copilot" / "llm" / "recorded_demo.json"


def make_fake():
    data = json.loads(_DEMO.read_text())
    return FakeLLMClient(rules=data["rules"], default_text=data["default_text"], model="claude-haiku-4-5")
