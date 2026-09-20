# Search and RAG

## Lexical search

```python
from scvp import InMemorySearchProvider, SearchDocument

search = InMemorySearchProvider()
search.index(SearchDocument("guide", "SCVP agents use memory"))
results = search.search("memory")
```

## Semantic retrieval

Install the optional embedding backend:

```bash
python -m pip install -e ".[embeddings]"
```

```python
from scvp import KnowledgeBase, SentenceTransformerEmbedder

knowledge = KnowledgeBase(embedder=SentenceTransformerEmbedder())
knowledge.ingest("guide", "SCVP stores searchable knowledge.")
context = knowledge.build_context("Where is knowledge stored?")
```

`KnowledgeBase` chunks documents, indexes chunks, stores embeddings, ranks by cosine similarity, and formats the retrieved context. Without an embedder it uses explicit lexical fallback.

## Google web search

Google search is external web search, not document indexing. Configure credentials only through the environment:

```powershell
$env:SCVP_SEARCH__GOOGLE__API_KEY="..."
$env:SCVP_SEARCH__GOOGLE__CX="..."
```

```python
from scvp import GoogleSearchProvider
results = GoogleSearchProvider().search("local AI", limit=5)
```
