# @sovereignempirex/scvp

JavaScript implementation of SCVP Phase 5 conversation memory.

The package also includes an HTTP client for the SCVP API:

```js
import { SCVPClient } from "@sovereignempirex/scvp";

const client = new SCVPClient({
	baseUrl: "http://127.0.0.1:8765",
	apiKey: process.env.SCVP_API_KEY,
});

await client.ingest("handbook", "SCVP knowledge is searchable.");
const results = await client.knowledgeSearch("searchable knowledge");
```

Node.js 18 or newer is required for the built-in `fetch` implementation.

```bash
npm install @sovereignempirex/scvp
```

```js
import { InMemoryProvider } from "@sovereignempirex/scvp";

const memory = new InMemoryProvider();
memory.save("support-1", { role: "user", content: "Remember my name is Sam." });
console.log(memory.load("support-1"));
```

The package is intentionally provider-agnostic. Persistent backends can extend
`MemoryProvider` without changing application code.