"""Phân loại lỗi provider (503 quá tải, 429 quota, sai key…) thành RunFailed có code/message rõ ràng."""

import pytest

from app.ai import ChatMessage, RunCompleted, RunContext, RunFailed, TextDelta
from app.ai.providers.base import ModelConfig, classify_provider_error
from app.ai.service import AIService


class _StatusCodeError(Exception):
    """Giống openai/anthropic: lỗi có .status_code"""

    def __init__(self, status_code: int, message: str = "error") -> None:
        super().__init__(message)
        self.status_code = status_code


class _GenaiError(Exception):
    """Giống google.genai.errors.APIError: lỗi có .code là int"""

    def __init__(self, code: int, message: str = "error") -> None:
        super().__init__(message)
        self.code = code


class ReadTimeout(Exception):
    """Tên giống httpx.ReadTimeout"""


GEMINI_503 = (
    "503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. "
    "Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}"
)


@pytest.mark.parametrize(
    ("exc", "expected_code"),
    [
        (Exception(GEMINI_503), "model_overloaded"),  # langchain_google_genai.GoogleAPIError: chỉ có message
        (_GenaiError(503), "model_overloaded"),
        (_StatusCodeError(529), "model_overloaded"),  # Anthropic overloaded
        (_StatusCodeError(429), "rate_limited"),
        (Exception("429 RESOURCE_EXHAUSTED. quota exceeded"), "rate_limited"),
        (_StatusCodeError(401), "provider_auth_error"),
        (_GenaiError(403), "provider_auth_error"),
        (_GenaiError(400, "400 INVALID_ARGUMENT. API key not valid. Please pass a valid API key."), "provider_auth_error"),
        (_StatusCodeError(404), "model_not_found"),
        (TimeoutError(), "provider_timeout"),
        (ReadTimeout(), "provider_timeout"),
    ],
)
def test_classify_known_errors(exc: Exception, expected_code: str):
    result = classify_provider_error(exc)
    assert result is not None
    assert result[0] == expected_code


@pytest.mark.parametrize(
    "exc",
    [
        Exception("something broke"),
        _GenaiError(400, "400 INVALID_ARGUMENT. Request contains an invalid argument."),
        _StatusCodeError(500),
    ],
)
def test_classify_unknown_errors_returns_none(exc: Exception):
    assert classify_provider_error(exc) is None


def test_classify_follows_wrapped_cause():
    """SDK hay bọc lỗi HTTP gốc: `raise WrapperError(...) from original`."""
    try:
        try:
            raise _GenaiError(503, "server error")
        except _GenaiError as original:
            raise RuntimeError("wrapped") from original
    except RuntimeError as wrapped:
        result = classify_provider_error(wrapped)

    assert result is not None and result[0] == "model_overloaded"


# ── AIService chuyển lỗi provider thành RunFailed ──────────────────────


class _FailingRunner:
    def __init__(self, exc: Exception, partial: str = "") -> None:
        self._exc = exc
        self._partial = partial

    async def run(self, ctx, prompt):
        if self._partial:
            yield TextDelta(content=self._partial)
        raise self._exc


def _ctx() -> RunContext:
    return RunContext(
        model=ModelConfig(provider="gemini", model_name="test-model"),
        messages=[ChatMessage(role="user", content="hi")],
    )


async def _collect(service: AIService) -> list:
    return [event async for event in service.stream(_ctx())]


async def test_service_reports_overloaded_model():
    events = await _collect(AIService(runners={"chat": _FailingRunner(Exception(GEMINI_503), partial="Xin")}))

    failed = events[-1]
    assert isinstance(failed, RunFailed)
    assert failed.code == "model_overloaded"
    assert "quá tải" in failed.message
    assert failed.partial_content == "Xin"
    assert not any(isinstance(e, RunCompleted) for e in events)


async def test_service_keeps_generic_message_for_unknown_errors():
    events = await _collect(AIService(runners={"chat": _FailingRunner(ValueError("boom"))}))

    failed = events[-1]
    assert isinstance(failed, RunFailed)
    assert failed.code == "provider_error"
    assert "ValueError" in failed.message
