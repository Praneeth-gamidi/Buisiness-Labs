from types import SimpleNamespace

import pytest

from llm_provider import LLMConfigurationError, LLMProviderError, generate_text


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        if self.error:
            raise self.error
        return self.response


def fake_client(response=None, error=None):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(response, error)))


def response_with(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_groq_config_requires_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(LLMConfigurationError, match="GROQ_API_KEY"):
        generate_text([], max_tokens=10, provider="groq")


def test_groq_returns_chat_completion_text():
    result = generate_text(
        [{"role": "user", "content": "hello"}],
        max_tokens=10,
        provider="groq",
        api_key="test-key",
        client=fake_client(response_with("hello")),
    )
    assert result == "hello"


def test_groq_uses_configured_model_and_completion_limit():
    client = fake_client(response_with("hello"))
    generate_text([], max_tokens=37, provider="groq", model="configured-model", api_key="test-key", client=client)
    request = client.chat.completions.request
    assert request["model"] == "configured-model"
    assert request["max_completion_tokens"] == 37


def test_groq_maps_rate_limit_without_leaking_provider_error():
    class RateLimitError(Exception):
        pass

    with pytest.raises(LLMProviderError) as error:
        generate_text([], max_tokens=10, provider="groq", api_key="test-key", client=fake_client(error=RateLimitError("secret detail")))
    assert error.value.code == "rate_limit"
    assert "secret detail" not in str(error.value)


def test_mock_provider_is_explicit_and_deterministic():
    result = generate_text([], max_tokens=10, provider="mock")
    assert "not genuine AI output" in result