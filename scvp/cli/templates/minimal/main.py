"""
Minimal SCVP starter.

Run:
    python main.py
"""

from scvp import Message, Role, SCVPModel, load_config


def main() -> None:
    config = load_config()
    provider = config.get("model.provider", "mock")

    model = SCVPModel(provider=provider)
    response = model.chat([Message(role=Role.USER, content="Hello, SCVP!")])

    print(f"[{response.provider}] {response.content}")


if __name__ == "__main__":
    main()
