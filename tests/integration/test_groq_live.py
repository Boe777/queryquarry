import pytest

from app.llm.client import GroqClient


@pytest.mark.integration
def test_live_model_responds() -> None:
    result = GroqClient().complete(
        [{"role": "user", "content": "Reply with the single word: ready"}]
    )

    assert "ready" in result.lower()
