from langchain_openai import ChatOpenAI

from app.ai.providers.base import ModelConfig
from app.ai.providers.factory import register_provider
from app.core.config import settings


@register_provider("ollama")
def build_ollama(config: ModelConfig) -> ChatOpenAI:
    # Dùng endpoint tương thích OpenAI của Ollama (`<host>/v1`) nên không cần thêm package langchain-ollama.
    # Ollama local không cần key (SDK OpenAI vẫn bắt phải có 1 chuỗi); Ollama Cloud thì cần OLLAMA_API_KEY.
    return ChatOpenAI(
        model=config.model_name,
        api_key=settings.OLLAMA_API_KEY or "ollama",
        base_url=settings.OLLAMA_BASE_URL,
        stream_usage=True,
        timeout=settings.AI_REQUEST_TIMEOUT,
        max_retries=settings.AI_MAX_RETRIES,
        **config.sampling_params(),
    )
