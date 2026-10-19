import pytest

from llm_provider import LLMOutputError
from task3_meeting_scope import agents


def test_malformed_stage_json_is_rejected(monkeypatch):
    monkeypatch.setattr(agents, "generate_text", lambda *_args, **_kwargs: "not json")
    with pytest.raises(LLMOutputError, match="malformed JSON for requirements analyst"):
        agents.ask_json("requirements analyst", "extract", "transcript", agents.Discovery)


def test_json_mode_and_schema_are_sent_to_groq(monkeypatch):
    request = {}
    valid = '{"goals":[],"users":[],"requested_features":[],"constraints":[],"acceptance_criteria":[],"open_questions":[]}'
    def fake_generate(messages, **kwargs):
        request["messages"] = messages
        request.update(kwargs)
        return valid
    monkeypatch.setattr(agents, "generate_text", fake_generate)

    agents.ask_json("requirements analyst", "extract", "transcript", agents.Discovery)

    assert request["response_format"] == {"type": "json_object"}
    assert "JSON Schema:" in request["messages"][1]["content"]


def test_invalid_scope_item_is_rejected(monkeypatch):
    invalid = '{"summary":"x","items":[{"name":"x","category":"invented","description":"x","acceptance_criteria":[]}],"assumptions":[],"exclusions":[],"unresolved_questions":[],"source_urls":[]}'
    monkeypatch.setattr(agents, "generate_text", lambda *_args, **_kwargs: invalid)
    with pytest.raises(LLMOutputError, match="items.0.category"):
        agents.ask_json("solution architect", "scope", "input", agents.Scope)


def test_scope_without_sources_defaults_to_empty_list(monkeypatch):
    valid_without_sources = '{"summary":"Defined scope","items":[],"assumptions":[],"exclusions":[],"unresolved_questions":[]}'
    monkeypatch.setattr(agents, "generate_text", lambda *_args, **_kwargs: valid_without_sources)
    assert agents.ask_json("solution architect", "scope", "input", agents.Scope)["source_urls"] == []


def test_mock_build_validates_all_steps_without_live_calls(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setattr(agents, "kb_lookup", lambda _question: {"answer": "No indexed evidence.", "sources": [], "needs_human": True})
    result = agents.build("A sample transcript")
    assert result["llm_provider"] == "mock"
    assert result["approval_required"] is True
    assert result["proposal"]["approval_required"] is True
    assert "Mock mode" in result["discovery"]["open_questions"][0]


def test_estimate_rejects_inconsistent_hour_ranges():
    with pytest.raises(ValueError):
        agents.EstimateTask(
            task="Build feature", low_hours=8, likely_hours=4, high_hours=10,
            roles=[], dependencies=[], assumptions=[], risks=[],
        )