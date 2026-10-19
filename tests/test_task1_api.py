import sys
from types import ModuleType

import pytest
import requests


store_stub = ModuleType("task1_knowledge_brain.store")
store_stub.retrieve = lambda _question, _k=5: []
store_stub.save_feedback = lambda *_args: None
store_stub.upsert = lambda *_args: None
store_stub.reconcile = lambda *_args: None
sys.modules["task1_knowledge_brain.store"] = store_stub

from task1_knowledge_brain import app as task1_app


def test_query_uses_retrieved_context_and_preserves_sources(monkeypatch):
    chunks = [{"title": "Account settings", "url": "https://example.test/settings", "text": "Use the account page to update settings."}]
    retrieved = []
    prompts = []
    monkeypatch.setattr(task1_app, "retrieve", lambda question, k: retrieved.append((question, k)) or chunks)
    monkeypatch.setattr(task1_app, "generate_text", lambda messages, **_kwargs: prompts.append(messages) or "Use the account page. [Source 1]")
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = task1_app.query(task1_app.Question(question="How do I update settings?", top_k=3))

    assert retrieved == [("How do I update settings?", 3)]
    assert "Use the account page to update settings." in prompts[0][1]["content"]
    assert "https://example.test/settings" in prompts[0][1]["content"]
    assert response["sources"][0]["url"] == "https://example.test/settings"
    assert response["llm_provider"] == "mock"
    assert response["needs_human"] is True


def test_query_without_evidence_does_not_call_llm(monkeypatch):
    monkeypatch.setattr(task1_app, "retrieve", lambda *_args: [])
    monkeypatch.setattr(task1_app, "generate_text", lambda *_args, **_kwargs: pytest.fail("LLM must not run without evidence"))

    response = task1_app.query(task1_app.Question(question="How do I update settings?"))

    assert response["sources"] == []
    assert response["needs_human"] is True


def test_ingest_skips_untrusted_hosts_and_does_not_reconcile_partial_crawls(monkeypatch):
    from task1_knowledge_brain import ingest as ingest_module

    trusted = "https://support.brilliantdirectories.com/article"
    untrusted = "https://support.brilliantdirectories.com.attacker.example/article"
    failed = "https://support.brilliantdirectories.com/unavailable"
    attempted = []
    upserted = []
    reconciled = []

    def fake_extract(url):
        attempted.append(url)
        if url == failed:
            raise requests.ConnectionError("fixture failure")
        return "Fixture", "x" * 100, ["x" * 100]

    monkeypatch.setattr(ingest_module, "sitemap_urls", lambda: [trusted, untrusted, failed])
    monkeypatch.setattr(ingest_module, "extract", fake_extract)
    monkeypatch.setattr(ingest_module, "upsert", lambda url, *_args: upserted.append(url))
    monkeypatch.setattr(ingest_module, "reconcile", lambda seen: reconciled.append(seen))
    monkeypatch.setattr(ingest_module, "DELAY", 0)

    ingest_module.ingest()

    assert attempted == [trusted, failed]
    assert upserted == [trusted]
    assert reconciled == []


def test_ingest_reconciles_after_a_complete_crawl_with_usable_content(monkeypatch):
    from task1_knowledge_brain import ingest as ingest_module

    trusted = "https://support.brilliantdirectories.com/article"
    reconciled = []
    monkeypatch.setattr(ingest_module, "sitemap_urls", lambda: [trusted])
    monkeypatch.setattr(ingest_module, "extract", lambda _url: ("Fixture", "x" * 100, ["x" * 100]))
    monkeypatch.setattr(ingest_module, "upsert", lambda *_args: None)
    monkeypatch.setattr(ingest_module, "reconcile", lambda seen: reconciled.append(seen))
    monkeypatch.setattr(ingest_module, "DELAY", 0)

    ingest_module.ingest()

    assert reconciled == [{trusted}]