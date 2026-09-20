# Plugins and SDKs

## Plugins

Implement `Plugin`, expose a `plugin` object, and publish it through the `scvp.plugins` entry-point group:

```toml
[project.entry-points."scvp.plugins"]
my_plugin = "my_package.plugin:plugin"
```

Lifecycle hooks are `load`, `enable`, `disable`, and `unload`. Services and configuration are provided through `PluginContext`.

```bash
scvp plugin list
```

## Python SDK

```python
from scvp import SCVPClient

client = SCVPClient("http://127.0.0.1:8765", api_key="scvp_...")
print(client.health())
client.ingest("guide", "SCVP knowledge")
print(client.knowledge_search("knowledge"))
```

## JavaScript SDK

```bash
npm install @sovereignempirex/scvp
```

```js
import { SCVPClient } from "@sovereignempirex/scvp";

const client = new SCVPClient({
  baseUrl: "http://127.0.0.1:8765",
  apiKey: process.env.SCVP_API_KEY,
});
console.log(await client.health());
```

Node.js 18+ is required for the built-in `fetch` implementation.
