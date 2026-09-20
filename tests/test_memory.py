import pytest

from scvp import Agent, InMemoryProvider, Message, Role, SCVPModel


def test_in_memory_provider_isolated_by_conversation():
    memory = InMemoryProvider()
    memory.save("one", Message(Role.USER, "hello"))
    memory.save("one", Message(Role.ASSISTANT, "hi"))
    memory.save("two", Message(Role.USER, "other"))

    assert [message.content for message in memory.load("one")] == ["hello", "hi"]
    assert [message.content for message in memory.load("two")] == ["other"]


def test_in_memory_provider_limit_and_delete():
    memory = InMemoryProvider()
    for content in ("one", "two", "three"):
        memory.save("chat", Message(Role.USER, content))

    assert [message.content for message in memory.load("chat", limit=2)] == ["two", "three"]
    memory.delete("chat")
    assert memory.load("chat") == []


def test_in_memory_provider_validates_inputs():
    memory = InMemoryProvider()
    with pytest.raises(ValueError):
        memory.save("", Message(Role.USER, "hello"))
    with pytest.raises(ValueError):
        memory.load("chat", limit=-1)


def test_agent_persists_conversation_when_requested():
    memory = InMemoryProvider()
    agent = Agent(model=SCVPModel("mock"), memory=memory)

    agent.run("hello", conversation_id="chat")

    messages = memory.load("chat")
    assert messages[-2].role == Role.USER
    assert messages[-2].content == "hello"
    assert messages[-1].role == Role.ASSISTANT