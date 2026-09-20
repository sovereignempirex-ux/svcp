/**
 * Provider-agnostic conversation memory for JavaScript.
 *
 * The API mirrors Python's MemoryProvider for the completed Phase 5 surface.
 */
export class MemoryProvider {
  save() {
    throw new Error("MemoryProvider.save() must be implemented by a provider.");
  }

  load() {
    throw new Error("MemoryProvider.load() must be implemented by a provider.");
  }

  delete() {
    throw new Error("MemoryProvider.delete() must be implemented by a provider.");
  }

  clear() {
    throw new Error("MemoryProvider.clear() must be implemented by a provider.");
  }
}

export class InMemoryProvider extends MemoryProvider {
  constructor() {
    super();
    this.conversations = new Map();
  }

  save(conversationId, message) {
    this.#validateConversationId(conversationId);
    if (!message || typeof message !== "object") {
      throw new TypeError("message must be an object.");
    }
    const messages = this.conversations.get(conversationId) ?? [];
    messages.push({ ...message });
    this.conversations.set(conversationId, messages);
  }

  load(conversationId, limit = undefined) {
    if (limit !== undefined && (!Number.isInteger(limit) || limit < 0)) {
      throw new RangeError("limit must be a non-negative integer.");
    }
    const messages = this.conversations.get(conversationId) ?? [];
    const selected = limit === undefined ? messages : limit === 0 ? [] : messages.slice(-limit);
    return selected.map((message) => ({ ...message }));
  }

  delete(conversationId) {
    this.conversations.delete(conversationId);
  }

  clear() {
    this.conversations.clear();
  }

  #validateConversationId(conversationId) {
    if (typeof conversationId !== "string" || conversationId.length === 0) {
      throw new TypeError("conversationId must not be empty.");
    }
  }
}

export const InMemoryMemory = InMemoryProvider;

export class SCVPAPIError extends Error {
  constructor(status, detail) {
    super(`SCVP API error${status ? ` (${status})` : ""}: ${detail}`);
    this.name = "SCVPAPIError";
    this.status = status;
    this.detail = detail;
  }
}

export class SCVPClient {
  constructor({ baseUrl = "http://127.0.0.1:8765", apiKey = undefined, fetchImpl = globalThis.fetch } = {}) {
    if (typeof fetchImpl !== "function") {
      throw new Error("SCVPClient requires fetch (Node 18+ or a fetch implementation).");
    }
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.fetch = fetchImpl;
  }

  health() { return this.#request("GET", "/health"); }

  ingest(documentId, content, metadata = {}) {
    return this.#request("POST", "/knowledge/documents", { id: documentId, content, metadata });
  }

  knowledgeSearch(query, limit = 5) {
    return this.#request("POST", "/knowledge/search", { query, limit });
  }

  webSearch(query, limit = 5, offset = 0) {
    return this.#request("POST", "/search", { query, limit, offset });
  }

  runAgent(goal, conversationId = undefined, metadata = {}) {
    return this.#request("POST", "/agents/run", { goal, conversation_id: conversationId, metadata });
  }

  async #request(method, path, body = undefined) {
    const headers = { Accept: "application/json" };
    if (this.apiKey) headers["X-API-Key"] = this.apiKey;
    const options = { method, headers };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await this.fetch(`${this.baseUrl}${path}`, options);
    const payload = await response.json();
    if (!response.ok) {
      throw new SCVPAPIError(response.status, payload.detail ?? "Request failed.");
    }
    return payload;
  }
}