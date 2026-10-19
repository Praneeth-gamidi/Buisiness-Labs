import Groq from "groq-sdk";

export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };
type ChatRequest = { model: string; messages: ChatMessage[]; max_completion_tokens: number };
type ChatResponse = { choices: Array<{ message: { content: string | null } }> };
export type ChatClient = { chat: { completions: { create: (request: ChatRequest) => Promise<ChatResponse> } } };

export class LLMConfigurationError extends Error {}
export class LLMProviderError extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
  }
}
export class LLMOutputError extends Error {}

export const providerName = () => (process.env.LLM_PROVIDER || "groq").trim().toLowerCase();
export const modelName = () => (process.env.GROQ_MODEL || "openai/gpt-oss-20b").trim();

export async function generateText(
  messages: ChatMessage[],
  maxTokens: number,
  options: { provider?: string; model?: string; apiKey?: string; client?: ChatClient } = {},
): Promise<string> {
  const provider = (options.provider || providerName()).trim().toLowerCase();
  const model = options.model || modelName();
  console.info(`[llm] provider=${provider} model=${model}`);

  if (provider === "mock") {
    return JSON.stringify({
      subject: "Re: customer request",
      reply: "Mock mode draft only. This is deterministic demo output, not genuine AI inference.",
      needsHuman: true,
      reason: "Mock output requires human review.",
    });
  }
  if (provider !== "groq") {
    throw new LLMConfigurationError(`Unsupported LLM_PROVIDER '${provider}'. Use 'groq' or 'mock'.`);
  }

  const apiKey = options.apiKey ?? process.env.GROQ_API_KEY;
  if (!apiKey) throw new LLMConfigurationError("GROQ_API_KEY is required when LLM_PROVIDER=groq.");
  const client = options.client || (new Groq({ apiKey, timeout: 30_000 }) as unknown as ChatClient);
  let response: ChatResponse;
  try {
    response = await client.chat.completions.create({ model, messages, max_completion_tokens: maxTokens });
  } catch (error) {
    const name = error instanceof Error ? error.name.toLowerCase() : "";
    const status = typeof error === "object" && error !== null && "status" in error ? error.status : undefined;
    if (name.includes("ratelimit") || status === 429) throw new LLMProviderError("rate_limit", "Groq rate limit reached. Try again later.");
    if (name.includes("timeout")) throw new LLMProviderError("timeout", "Groq request timed out. Try again.");
    if (name.includes("connection")) throw new LLMProviderError("connection", "Could not connect to Groq. Check the network and try again.");
    if (name.includes("authentication") || status === 401) throw new LLMProviderError("authentication", "Groq rejected the API key. Check GROQ_API_KEY.");
    throw new LLMProviderError("provider_error", "Groq could not complete the request.");
  }

  const content = response.choices[0]?.message.content;
  if (!content?.trim()) throw new LLMProviderError("empty_response", "Groq returned an empty response.");
  return content;
}

export function parseJsonObject<T extends Record<string, unknown>>(content: string): T {
  try {
    const value: unknown = JSON.parse(content);
    if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error();
    return value as T;
  } catch {
    throw new LLMOutputError("The model returned invalid JSON; no draft was accepted.");
  }
}