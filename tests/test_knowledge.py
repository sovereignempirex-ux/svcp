import pytest

from scvp import KnowledgeBase, TextChunker


class FakeSemanticEmbedder:
    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([
                float("python" in lowered),
                float("memory" in lowered),
                float("search" in lowered),
            ])
        return vectors


def test_text_chunker_creates_overlapping_chunks():
    chunks = TextChunker(chunk_size=10, overlap=2).split("abcdefghij12345")

    assert chunks == ["abcdefghij", "ij12345"]


def test_knowledge_base_ingests_and_retrieves_chunks():
    knowledge = KnowledgeBase(chunker=TextChunker(chunk_size=20, overlap=0))
    assert knowledge.ingest("guide", "SCVP uses search and memory.", {"url": "guide.md"}) == 2

    chunks = knowledge.retrieve("memory")

    assert len(chunks) == 1
    assert chunks[0].document_id == "guide"
    assert chunks[0].metadata == {"url": "guide.md"}


def test_knowledge_base_replaces_documents_and_builds_context():
    knowledge = KnowledgeBase(chunker=TextChunker(chunk_size=100, overlap=0))
    knowledge.ingest("faq", "Old answer")
    knowledge.ingest("faq", "New answer about SCVP")

    assert "New answer" in knowledge.build_context("SCVP")
    assert "Old answer" not in knowledge.build_context("answer")


def test_knowledge_base_delete_and_clear():
    knowledge = KnowledgeBase()
    knowledge.ingest("one", "first content")
    knowledge.ingest("two", "second content")
    knowledge.delete("one")
    assert knowledge.retrieve("first") == []
    knowledge.clear()
    assert knowledge.retrieve("second") == []


def test_chunker_validates_configuration():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=10, overlap=10)


def test_knowledge_base_can_retrieve_with_real_embedding_contract():
    knowledge = KnowledgeBase(
        chunker=TextChunker(chunk_size=100, overlap=0),
        embedder=FakeSemanticEmbedder(),
    )
    knowledge.ingest("python", "Python runtime guide")
    knowledge.ingest("memory", "Conversation memory guide")

    results = knowledge.retrieve("python programming")

    assert results[0].document_id == "python"
    assert results[0].score > 0