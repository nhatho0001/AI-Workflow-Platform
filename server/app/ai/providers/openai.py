from langchain_openai import ChatOpenAI

from app.ai.providers.base import ModelConfig, require_setting
from app.ai.providers.factory import register_provider
from app.core.config import settings


@register_provider("openai")
def build_openai(config: ModelConfig) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model_name,
        api_key=require_setting(settings.OPENAI_API_KEY, "OPENAI_API_KEY", "openai"),
        base_url=settings.OPENAI_BASE_URL,
        stream_usage=True,  # để chunk cuối có usage_metadata (token count)
        timeout=settings.AI_REQUEST_TIMEOUT,
        max_retries=settings.AI_MAX_RETRIES,
        **config.sampling_params(),
    )
