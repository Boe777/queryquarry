import httpx
import pytest
import respx

from app.llm.client import GroqClient, LLMError, LLMRateLimitError

_URL = "https://api.groq.com/openai/v1/chat/completions"


def _client() -> GroqClient:
    return GroqClient(api_key="test-key", model="test-model", backoff_base=0.0)


def _ok(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


@respx.mock
def test_returns_assistant_content() -> None:
    respx.post(_URL).mock(return_value=_ok("select 1"))

    result = _client().complete([{"role": "user", "content": "hi"}])

    assert result == "select 1"


@respx.mock
def test_sends_model_and_messages() -> None:
    route = respx.post(_URL).mock(return_value=_ok("ok"))

    _client().complete([{"role": "user", "content": "hi"}])

    sent = route.calls.last.request
    assert b'"model":"test-model"' in sent.content
    assert sent.headers["authorization"] == "Bearer test-key"


@respx.mock
def test_retries_after_rate_limit_then_succeeds() -> None:
    route = respx.post(_URL).mock(side_effect=[httpx.Response(429), _ok("recovered")])

    result = _client().complete([{"role": "user", "content": "hi"}])

    assert result == "recovered"
    assert route.call_count == 2


@respx.mock
def test_gives_up_after_three_attempts() -> None:
    route = respx.post(_URL).mock(return_value=httpx.Response(429))

    with pytest.raises(LLMRateLimitError):
        _client().complete([{"role": "user", "content": "hi"}])

    assert route.call_count == 3


@respx.mock
def test_does_not_retry_on_bad_credentials() -> None:
    route = respx.post(_URL).mock(return_value=httpx.Response(401))

    with pytest.raises(LLMError):
        _client().complete([{"role": "user", "content": "hi"}])

    assert route.call_count == 1


@respx.mock
def test_rejects_empty_content() -> None:
    respx.post(_URL).mock(return_value=_ok("   "))

    with pytest.raises(LLMError, match="empty content"):
        _client().complete([{"role": "user", "content": "hi"}])
