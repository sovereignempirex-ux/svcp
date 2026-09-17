"""
SCVP Quickstart
=================
Mirrors the target developer experience from the SCVP spec:

    from scvp import Agent
    agent = Agent(name="CustomerSupport", model="scvp", tools=["search", "knowledge"])
    response = agent.run("Help the customer with their order.")

`Agent` doesn't exist yet -- it ships in Phase 3 (Agent Runtime). This
script shows what IS real today: the Model Layer, wired end to end
through Core (config, registry, types) with zero external dependencies.

Run:
    python examples/quickstart.py
"""

from scvp import Message, Role, SCVPModel


def main() -> None:
    model = SCVPModel(provider="mock")

    print("-- chat() --")
    response = model.chat(
        [Message(role=Role.USER, content="Help the customer with their order.")]
    )
    print(response.content)

    print("\n-- stream() --")
    for chunk in model.stream([Message(role=Role.USER, content="Stream me a reply")]):
        print(chunk.delta, end="", flush=True)
    print()

    print("\n-- embed() --")
    vectors = model.embed(["order status", "refund policy"])
    print(f"{len(vectors)} vectors, dim={len(vectors[0])}")

    print("\n-- classify() --")
    label = model.classify("Where is my package?", labels=["shipping", "billing", "returns"])
    print(f"classified as: {label}")


if __name__ == "__main__":
    main()
