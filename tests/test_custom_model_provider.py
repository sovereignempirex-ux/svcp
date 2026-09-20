import time

import pytest

from scvp import Message, Role, SCVPModel
from scvp.core.config import load_config
from scvp.core.exceptions import ModelError, SCVPTimeoutError
from scvp.models.base import model_registry
from scvp.models.providers.custom import CustomModelProvider
from scvp.models.providers.mock import MockModelProvider


def test_custom_provider_is_registered():
    assert model_registry.is_registered("custom")


def test_custom_config_schema_is_read(tmp_path):
    config_file = tmp_path / "scvp.config.yaml"
    config_file.write_text(
        "models:\n"
        "  default: custom\n"
        "  providers:\n"
        "    custom:\n"
        "      type: custom\n"
        "      model_path: ./models/my-model\n"
        "      device: auto\n"
        "      temperature: 0.7\n"
        "      max_tokens: 512\n",
        encoding="utf-8",
    )
    config = load_config(path=str(config_file))
    assert config.get("models.default") == "custom"
    assert config.get("models.providers.custom.model_path") == "./models/my-model"


def test_custom_provider_can_be_created_with_injected_mock():
    provider = CustomModelProvider(model=MockModelProvider(), model_name="test-model")
    response = provider.generate("hello local model")
    assert response.provider == "custom"
    assert response.model == "test-model"
    assert "hello local model" in response.content


def test_custom_model_from_config_accepts_type_field():
    config = load_config(
        overrides={
            "models": {
                "default": "custom",
                "providers": {"custom": {"type": "custom", "model": MockModelProvider()}},
            }
        }
    )
    model = SCVPModel.from_config(config)
    assert model.provider_name == "custom"
    assert "hello" in model.generate("hello").content


def test_custom_provider_reports_missing_local_model():
    with pytest.raises(ModelError, match="requires model_path"):
        CustomModelProvider().generate("hello")


def test_custom_provider_reports_timeout():
    class SlowModel:
        def generate(self, prompt, **kwargs):
            time.sleep(0.05)
            return "late"

    provider = CustomModelProvider(model=SlowModel(), timeout=0.001)
    with pytest.raises(SCVPTimeoutError):
        provider.chat([Message(role=Role.USER, content="hello")])


def test_custom_provider_streams_in_chunks():
    provider = CustomModelProvider(model=MockModelProvider())
    chunks = list(provider.stream([Message(role=Role.USER, content="stream me")]))
    assert chunks[-1].done is True
    assert "stream me" in "".join(chunk.delta for chunk in chunks)