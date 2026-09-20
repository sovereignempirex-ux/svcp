from scvp import Message, Role
from scvp.models.base import model_registry
from scvp.models.providers.local import LocalModelProvider


def test_real_local_provider_is_registered_and_uses_local_backend_contract():
    assert model_registry.is_registered("local")

    class LocalBackend:
        def generate(self, prompt, **kwargs):
            return "local answer: " + prompt

    provider = LocalModelProvider(model=LocalBackend(), model_name="my-local-model")
    response = provider.chat([Message(Role.USER, "hello")])

    assert response.provider == "local"
    assert response.model == "my-local-model"
    assert response.content == "local answer: user: hello"