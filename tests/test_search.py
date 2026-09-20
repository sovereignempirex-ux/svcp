import pytest

from scvp import InMemorySearchProvider, SearchDocument


def test_in_memory_search_ranks_by_token_frequency():
    search = InMemorySearchProvider()
    search.index(SearchDocument("one", "Python agents use tools."))
    search.index(SearchDocument("two", "Python Python memory and tools."))
    search.index(SearchDocument("three", "Unrelated content."))

    results = search.search("python tools")

    assert [result.document.id for result in results] == ["two", "one"]
    assert results[0].score == 3.0


def test_search_replaces_documents_and_supports_pagination():
    search = InMemorySearchProvider()
    search.index(SearchDocument("b", "shared topic"))
    search.index(SearchDocument("a", "shared topic"))
    search.index(SearchDocument("a", "shared topic revised"))

    results = search.search("shared", limit=1, offset=1)

    assert [result.document.id for result in results] == ["b"]


def test_search_validates_documents_and_ranges():
    search = InMemorySearchProvider()
    with pytest.raises(ValueError):
        search.index(SearchDocument("", "content"))
    with pytest.raises(ValueError):
        search.search("content", limit=-1)
    with pytest.raises(ValueError):
        search.search("content", offset=-1)
    assert search.search("   ") == []


def test_search_delete_and_clear():
    search = InMemorySearchProvider()
    search.index(SearchDocument("one", "content"))
    search.delete("one")
    assert search.search("content") == []
    search.index(SearchDocument("two", "content"))
    search.clear()
    assert search.search("content") == []