import logging
import os
from typing import Any


logger = logging.getLogger(__name__)
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class LLMOutputError(RuntimeError):
    pass


def provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "groq").strip().lower()


def model_name() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()


def _mock_response(messages: list[dict[str, str]]) -> str:
    system = messages[0]["content"].lower() if messages else ""
    if "requirements analyst" in system:
        return '{"goals":[],"users":[],"requested_features":[],"constraints":[],"acceptance_criteria":[],"open_questions":["Mock mode does not analyze transcript content."]}'
    if "solution architect" in system:
        return '{"summary":"Mock scope; requirements were not analyzed.","items":[{"name":"Requirements review","category":"needs_clarification","description":"Review the transcript with a human.","acceptance_criteria":[]}],"assumptions":[],"exclusions":[],"unresolved_questions":["Mock mode does not analyze transcript content."],"source_urls":[]}'
    if "developer estimator" in system:
        return '{"summary":"No estimate generated in mock mode.","tasks":[],"unresolved_items":["A human must estimate after requirements review."]}'
    if "proposal writer" in system:
        return '{"summary":"Mock proposal; not client-ready.","scope_items":[],"deliverables":[],"timeline_assumptions":[],"estimate_summary":"Not estimated in mock mode.","exclusions":[],"risks":["Mock mode does not analyze transcript content."],"questions":["Review requirements with a human."],"approval_required":true}'
    if "scope change analyst" in system:
        return '{"unchanged":[],"changed":[],"new":[],"removed":[],"out_of_scope_flags":[],"human_review_required":true}'
    return "Mock mode: this is a deterministic demo response, not genuine AI output. [Source 1]"


def generate_text(
    messages: list[dict[str, str]],
    *,
    max_tokens: int,
    response_format: dict[str, str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    client: Any | None = None,
) -> str:
    selected_provider = (provider or provider_name()).strip().lower()
    selected_model = model or model_name()
    logger.info("Using LLM provider=%s model=%s", selected_provider, selected_model)

    if selected_provider == "mock":
        return _mock_response(messages)
    if selected_provider != "groq":
        raise LLMConfigurationError(f"Unsupported LLM_PROVIDER '{selected_provider}'. Use 'groq' or 'mock'.")

    selected_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY", "")
    if not selected_key:
        raise LLMConfigurationError("GROQ_API_KEY is required when LLM_PROVIDER=groq.")
    if client is None:
        try:
            from groq import Groq
        except ImportError as error:
            raise LLMConfigurationError("Install the Python dependencies to use the Groq provider.") from error
        client = Groq(api_key=selected_key, timeout=30.0)

    request: dict[str, Any] = {"model": selected_model, "messages": messages, "max_completion_tokens": max_tokens}
    if response_format is not None:
        request["response_format"] = response_format
    try:
        result = client.chat.completions.create(**request)
    except Exception as error:
        error_name = type(error).__name__.lower()
        status_code = getattr(error, "status_code", None)
        if "ratelimit" in error_name or status_code == 429:
            raise LLMProviderError("rate_limit", "Groq rate limit reached. Try again later.") from None
        if "timeout" in error_name:
            raise LLMProviderError("timeout", "Groq request timed out. Try again.") from None
        if "connection" in error_name:
            raise LLMProviderError("connection", "Could not connect to Groq. Check the network and try again.") from None
        if "authentication" in error_name or status_code == 401:
            raise LLMProviderError("authentication", "Groq rejected the API key. Check GROQ_API_KEY.") from None
        raise LLMProviderError("provider_error", "Groq could not complete the request.") from None

    try:
        content = result.choices[0].message.content
    except (AttributeError, IndexError, TypeError):
        content = None
    if not isinstance(content, str) or not content.strip():
        raise LLMProviderError("empty_response", "Groq returned an empty response.")
    return content