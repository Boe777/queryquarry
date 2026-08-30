import time
from typing import Any

import httpx

from app.config import get_settings

Message = dict[str, str]

_RETRYABLE_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504})


class LLMError(RuntimeError):
    """Anything that goes wrong while talking to the model."""


class LLMRateLimitError(LLMError):
    """The provider asked us to slow down."""


class LLMUnavailableError(LLMError):
    """The provider could not be reached or failed on its side."""


class GroqClient:
    """Thin wrapper over the Groq chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 60.0,
        max_attempts: int = 3,
        backoff_base: float = 1.0,
    ) -> None:
        if api_key is None or model is None:
            settings = get_settings()
            api_key = api_key if api_key is not None else settings.groq_api_key
            model = model if model is not None else settings.groq_model

        if not api_key:
            raise LLMError("GROQ_API_KEY is not set")

        self._api_key = api_key
        self._model = model
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        """Send a chat request and return the assistant's text."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        last_error: LLMError = LLMUnavailableError("no attempt was made")

        for attempt in range(1, self._max_attempts + 1):
            wait_hint: float | None = None

            try:
                response = httpx.post(
                    self._url, json=payload, headers=headers, timeout=self._timeout
                )
            except httpx.RequestError as exc:
                last_error = LLMUnavailableError(f"could not reach the provider: {exc}")
            else:
                if response.status_code == 200:
                    return _extract_text(response.json())

                if response.status_code not in _RETRYABLE_STATUS:
                    raise LLMError(f"provider returned {response.status_code}")

                if response.status_code == 429:
                    last_error = LLMRateLimitError("provider rate limit reached")
                    wait_hint = _retry_after_seconds(response)
                else:
                    last_error = LLMUnavailableError(f"provider returned {response.status_code}")

            if attempt < self._max_attempts:
                delay = (
                    wait_hint if wait_hint is not None else self._backoff_base * 2 ** (attempt - 1)
                )
                time.sleep(delay)

        raise last_error


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_text(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("unexpected response shape") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMError("model returned empty content")

    return content
