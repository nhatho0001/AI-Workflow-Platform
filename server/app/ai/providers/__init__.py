"""Tầng provider. Import các adapter ở đây để chúng tự đăng ký vào registry của factory."""
from app.ai.providers import anthropic, ollama, openai, openrouter  # noqa: F401
from app.ai.providers.base import (
    AIEngineError,
    ModelConfig,
    ProviderNotConfiguredError,
    UnknownProviderError,
)
from app.ai.providers.factory import create_chat_model, register_provider, registered_providers

__all__ = [
    "AIEngineError",
    "ModelConfig",
    "ProviderNotConfiguredError",
    "UnknownProviderError",
    "create_chat_model",
    "register_provider",
    "registered_providers",
]
