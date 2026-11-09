from langchain_anthropic import ChatAnthropic

from app.ai.providers.base import ModelConfig, require_setting
from app.ai.providers.factory import register_provider
from app.core.config import settings


@register_provider("anthropic")
def build_anthropic(config: ModelConfig) -> ChatAnthropic:
    # Chỉ truyền tham số khác None: nhiều model Claude mới không cho đặt cùng lúc temperature và top_p.
    return ChatAnthropic(
        model=config.model_name,
        api_key=require_setting(settings.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY", "anthropic"),
        timeout=settings.AI_REQUEST_TIMEOUT,
        max_retries=settings.AI_MAX_RETRIES,
        **config.sampling_params(),
    )
