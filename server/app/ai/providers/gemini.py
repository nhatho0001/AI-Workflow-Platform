from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.providers.base import ModelConfig
from app.ai.providers.factory import register_provider
from app.core.config import settings


@register_provider("gemini")
def build_gemini(config: ModelConfig):

    def build_gemini(config: ModelConfig) -> ChatGoogleGenerativeAI:
       return ChatGoogleGenerativeAI(
            model=config.model_name,
            api_key=settings.GEMINI_API_KEY or "gemini",
            timeout=settings.AI_REQUEST_TIMEOUT,
            max_retries=settings.AI_MAX_RETRIES,
            **config.sampling_params(), 
       )