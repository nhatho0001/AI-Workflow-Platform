"""
Registry provider → adapter.

Thêm provider mới: viết 1 file trong `app/ai/providers/`, gắn `@register_provider("<key>")`,
rồi import file đó trong `app/ai/providers/__init__.py`. Key phải trùng giá trị `AIModelProvider`.
"""
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.ai.providers.base import ModelConfig, ProviderBuilder, UnknownProviderError

_registry: dict[str, ProviderBuilder] = {}


def register_provider(key: str):
    def decorator(builder: ProviderBuilder) -> ProviderBuilder:
        if key in _registry:
            raise ValueError(f"Provider '{key}' đã được đăng ký")
        _registry[key] = builder
        return builder

    return decorator


def registered_providers() -> list[str]:
    return sorted(_registry)


# ModelConfig frozen nên hashable → tái sử dụng client (và connection pool HTTP) cho cùng cấu hình.
# Lỗi (thiếu key, provider lạ) không bị cache, sửa .env + restart là chạy.
@lru_cache(maxsize=128)
def create_chat_model(config: ModelConfig) -> BaseChatModel:
    builder = _registry.get(config.provider)
    if builder is None:
        raise UnknownProviderError(f"Provider '{config.provider}' chưa được hỗ trợ")
    return builder(config)
