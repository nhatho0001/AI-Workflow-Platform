from langchain_openai import ChatOpenAI

from app.ai.providers.base import ModelConfig, require_setting
from app.ai.providers.factory import register_provider
from app.core.config import settings


@register_provider("openrouter")
def build_openrouter(config: ModelConfig) -> ChatOpenAI:
    # OpenRouter dùng API tương thích OpenAI; model_name dạng "anthropic/claude-sonnet-4.5", "meta-llama/..."
    return ChatOpenAI(
        model=config.model_name,
        api_key=require_setting(settings.OPENROUTER_API_KEY, "OPENROUTER_API_KEY", "openrouter"),
        base_url=settings.OPENROUTER_BASE_URL,
        default_headers={"X-Title": settings.APP_NAME},
        stream_usage=True,
        timeout=settings.AI_REQUEST_TIMEOUT,
        max_retries=settings.AI_MAX_RETRIES,
        **config.sampling_params(),
    )
