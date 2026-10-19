import json
import os
from typing import Literal, TypeVar

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, model_validator

from llm_provider import LLMOutputError, generate_text, provider_name

load_dotenv()
ModelType = TypeVar("ModelType", bound=BaseModel)


class Discovery(BaseModel):
	goals: list[str]
	users: list[str]
	requested_features: list[str]
	constraints: list[str]
	acceptance_criteria: list[str]
	open_questions: list[str]


class ScopeItem(BaseModel):
	name: str
	category: str = Field(pattern="^(existing_setting|custom_work|needs_clarification)$")
	description: str
	acceptance_criteria: list[str]


class Scope(BaseModel):
	summary: str
	items: list[ScopeItem]
	assumptions: list[str]
	exclusions: list[str]
	unresolved_questions: list[str]
	source_urls: list[str] = Field(default_factory=list)


class EstimateTask(BaseModel):
	task: str
	low_hours: float = Field(ge=0)
	likely_hours: float = Field(ge=0)
	high_hours: float = Field(ge=0)
	roles: list[str]
	dependencies: list[str]
	assumptions: list[str]
	risks: list[str]

	@model_validator(mode="after")
	def validate_hour_range(self):
		if not self.low_hours <= self.likely_hours <= self.high_hours:
			raise ValueError("Hours must be ordered low <= likely <= high")
		return self


class Estimate(BaseModel):
	summary: str
	tasks: list[EstimateTask]
	unresolved_items: list[str]


class Proposal(BaseModel):
	summary: str
	scope_items: list[str]
	deliverables: list[str]
	timeline_assumptions: list[str]
	estimate_summary: str
	exclusions: list[str]
	risks: list[str]
	questions: list[str]
	approval_required: Literal[True]


class ChangeReport(BaseModel):
	unchanged: list[str]
	changed: list[str]
	new: list[str]
	removed: list[str]
	out_of_scope_flags: list[str]
	human_review_required: Literal[True]


def kb_lookup(question: str) -> dict:
	try:
		response = requests.post(
			os.getenv("TASK1_BASE_URL", "http://localhost:8000") + "/query",
			json={"question": question, "top_k": 5},
			timeout=60,
		)
		response.raise_for_status()
		return response.json()
	except requests.RequestException:
		raise RuntimeError("Knowledge Brain request failed. Check that Task 1 is running and reachable.") from None


def ask_json(role: str, instruction: str, content: str, schema: type[ModelType]) -> dict:
	system = f"You are the {role}. Be precise, label assumptions, and never invent facts. Return only one valid JSON object matching the JSON Schema provided by the user. Represent missing information explicitly as questions or unresolved items."
	raw = generate_text(
		[
			{"role": "system", "content": system},
			{"role": "user", "content": instruction + "\n\nJSON Schema:\n" + json.dumps(schema.model_json_schema()) + "\n\nINPUT:\n" + content},
		],
		max_tokens=1600,
		response_format={"type": "json_object"},
	)
	normalized = raw.strip()
	try:
		parsed = json.loads(normalized)
	except json.JSONDecodeError:
		raise LLMOutputError(f"The model returned malformed JSON for {role}; no output was accepted.") from None
	try:
		return schema.model_validate(parsed).model_dump(mode="json")
	except ValidationError as error:
		fields = sorted({".".join(str(part) for part in issue["loc"]) or "<root>" for issue in error.errors()})
		raise LLMOutputError(f"The model returned {role} JSON that does not match the required schema (fields: {', '.join(fields)}). No output was accepted.") from None
	except TypeError:
		raise LLMOutputError(f"The model returned an invalid {role} JSON value; no output was accepted.") from None


def build(transcript: str, previous: dict | None = None) -> dict:
	discovery = ask_json(
		"requirements analyst",
		"Extract goals, users, requested features, constraints, acceptance criteria, and open questions. Use exactly these keys: goals, users, requested_features, constraints, acceptance_criteria, open_questions.",
		transcript,
		Discovery,
	)
	knowledge = kb_lookup("Check whether existing product settings/features could address this request: " + transcript[:3500])
	scope = ask_json(
		"solution architect",
		"Create scope JSON with keys summary, items, assumptions, exclusions, unresolved_questions, source_urls. Each item needs name, category (existing_setting, custom_work, or needs_clarification), description, acceptance_criteria. Do not treat uncertain knowledge as fact.",
		json.dumps({"discovery": discovery, "knowledge": knowledge}),
		Scope,
	)
	estimate = ask_json(
		"developer estimator",
		"Return JSON with summary, tasks, unresolved_items. Each task needs task, low_hours, likely_hours, high_hours, roles, dependencies, assumptions, risks. Keep low <= likely <= high. Avoid false precision and do not estimate unresolved work.",
		json.dumps({"scope": scope, "discovery": discovery}),
		Estimate,
	)
	proposal = ask_json(
		"proposal writer",
		"Return JSON with summary, scope_items, deliverables, timeline_assumptions, estimate_summary, exclusions, risks, questions, approval_required. Set approval_required=true. Do not add requirements, prices, or timelines absent from the input.",
		json.dumps({"scope": scope, "estimate": estimate}),
		Proposal,
	)
	change_report = None
	if previous is not None:
		change_report = ask_json(
			"scope change analyst",
			"Return JSON with unchanged, changed, new, removed, out_of_scope_flags, human_review_required. Compare only stated content and set human_review_required=true.",
			json.dumps({"previous": previous, "new": scope}),
			ChangeReport,
		)
	return {
		"llm_provider": provider_name(),
		"discovery": discovery,
		"knowledge_lookup": knowledge,
		"scope": scope,
		"estimate": estimate,
		"proposal": proposal,
		"change_report": change_report,
		"approval_required": True,
	}
