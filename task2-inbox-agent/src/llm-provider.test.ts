import assert from "node:assert/strict";
import test from "node:test";
import { generateText, LLMConfigurationError, LLMOutputError, LLMProviderError, parseJsonObject, type ChatClient } from "./llm-provider.js";
import { draftReply } from "./service.js";

const messages = [{ role: "user" as const, content: "hello" }];
const client = (content: string): ChatClient => ({
  chat: { completions: { create: async () => ({ choices: [{ message: { content } }] }) } },
});

test("Groq completion returns response text", async () => {
  assert.equal(await generateText(messages, 20, { provider: "groq", apiKey: "test", client: client("hello") }), "hello");
});

test("configured model and completion limit are sent to Groq", async () => {
  const configuredClient: ChatClient = {
    chat: { completions: { create: async (request) => {
      assert.equal(request.model, "configured-model");
      assert.equal(request.max_completion_tokens, 37);
      return { choices: [{ message: { content: "ok" } }] };
    } } },
  };
  await generateText(messages, 37, { provider: "groq", model: "configured-model", apiKey: "test", client: configuredClient });
});

test("missing Groq key is a configuration error", async () => {
  await assert.rejects(generateText(messages, 20, { provider: "groq", apiKey: "" }), LLMConfigurationError);
});

test("rate limit errors are safe to show", async () => {
  const rateLimited: ChatClient = { chat: { completions: { create: async () => { throw Object.assign(new Error("secret detail"), { status: 429 }); } } } };
  await assert.rejects(generateText(messages, 20, { provider: "groq", apiKey: "test", client: rateLimited }), (error: unknown) => error instanceof LLMProviderError && error.code === "rate_limit" && !error.message.includes("secret"));
});

test("malformed JSON is rejected instead of passed downstream", () => {
  assert.throws(() => parseJsonObject("not json"), LLMOutputError);
});

test("mock mode is explicitly deterministic demo output", async () => {
  const output = await generateText(messages, 20, { provider: "mock" });
  assert.match(output, /not genuine AI inference/);
});

test("inbox workflow calls Knowledge Brain and keeps mock draft for human review", async () => {
  const previousProvider = process.env.LLM_PROVIDER;
  const previousFetch = globalThis.fetch;
  process.env.LLM_PROVIDER = "mock";
  globalThis.fetch = async (_input, init) => {
    assert.ok(init?.signal instanceof AbortSignal);
    return new Response(JSON.stringify({ answer: "No indexed evidence.", sources: [], needs_human: true }));
  };
  try {
    const result = await draftReply({ id: "demo", subject: "Question", body: "Need help" });
    const draft = JSON.parse(result.draft) as { reply: string; needsHuman: boolean };
    assert.equal(result.llmProvider, "mock");
    assert.equal(result.requiresHumanReview, true);
    assert.match(draft.reply, /not genuine AI inference/);
    assert.equal(draft.needsHuman, true);
  } finally {
    globalThis.fetch = previousFetch;
    if (previousProvider === undefined) delete process.env.LLM_PROVIDER;
    else process.env.LLM_PROVIDER = previousProvider;
  }
});

test("inbox workflow rejects an invalid Knowledge Brain response", async () => {
  const previousProvider = process.env.LLM_PROVIDER;
  const previousFetch = globalThis.fetch;
  process.env.LLM_PROVIDER = "mock";
  globalThis.fetch = async () => new Response(JSON.stringify({ answer: "No evidence.", sources: [], needs_human: "yes" }));
  try {
    await assert.rejects(draftReply({ id: "demo", subject: "Question", body: "Need help" }));
  } finally {
    globalThis.fetch = previousFetch;
    if (previousProvider === undefined) delete process.env.LLM_PROVIDER;
    else process.env.LLM_PROVIDER = previousProvider;
  }
});

test("inbox workflow surfaces Task 1 timeouts", async () => {
  const previousProvider = process.env.LLM_PROVIDER;
  const previousFetch = globalThis.fetch;
  process.env.LLM_PROVIDER = "mock";
  globalThis.fetch = async () => { throw new DOMException("Timed out", "TimeoutError"); };
  try {
    await assert.rejects(draftReply({ id: "demo", subject: "Question", body: "Need help" }), { name: "TimeoutError" });
  } finally {
    globalThis.fetch = previousFetch;
    if (previousProvider === undefined) delete process.env.LLM_PROVIDER;
    else process.env.LLM_PROVIDER = previousProvider;
  }
});