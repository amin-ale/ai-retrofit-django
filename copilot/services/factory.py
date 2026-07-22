import json
from pathlib import Path

from copilot.llm.anthropic_client import AnthropicLLMClient
from copilot.llm.embeddings import HashingEmbeddingClient, VoyageEmbeddingClient
from copilot.llm.fake_client import FakeLLMClient

from .config import get

_DEMO_RULES_PATH = Path(__file__).resolve().parent.parent / "llm" / "recorded_demo.json"


def _load_demo_rules():
    if not _DEMO_RULES_PATH.exists():
        return [], ""
    data = json.loads(_DEMO_RULES_PATH.read_text())
    return data.get("rules", []), data.get("default_text", "")


def build_llm_client():
    backend = get("LLM_BACKEND")
    if backend == "anthropic":
        return AnthropicLLMClient(
            api_key=get("ANTHROPIC_API_KEY"),
            base_url=get("ANTHROPIC_BASE_URL"),
            version=get("ANTHROPIC_VERSION"),
            model=get("MODEL"),
            timeout=get("REQUEST_TIMEOUT"),
        )
    rules, default_text = _load_demo_rules()
    return FakeLLMClient(rules=rules, default_text=default_text, model=get("MODEL"))


def build_embedding_client():
    backend = get("EMBEDDING_BACKEND")
    if backend == "voyage":
        return VoyageEmbeddingClient(
            api_key=get("VOYAGE_API_KEY"),
            base_url=get("VOYAGE_BASE_URL"),
            model=get("VOYAGE_MODEL"),
            timeout=get("REQUEST_TIMEOUT"),
        )
    return HashingEmbeddingClient(dim=get("EMBEDDING_DIM"))
