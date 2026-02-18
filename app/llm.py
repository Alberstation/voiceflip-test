"""
LLM via Hugging Face Inference API (remote).
Primary model + up to two fallbacks on 402 Payment Required (free-tier models).
"""
import structlog
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.config import settings

logger = structlog.get_logger()


def _is_payment_required_or_retryable(exc: Exception) -> bool:
    """True if we should try the next model (402, payment required, or quota)."""
    msg = str(exc).lower()
    return (
        "402" in msg
        or "payment required" in msg
        or "quota" in msg
        or "rate limit" in msg
    )


def _make_hf_llm(repo_id: str) -> ChatHuggingFace:
    """Build a single ChatHuggingFace for the given repo_id."""
    endpoint = HuggingFaceEndpoint(
        repo_id=repo_id,
        task="text-generation",
        huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        max_new_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
        top_p=settings.llm_top_p,
    )
    return ChatHuggingFace(llm=endpoint)


def _llm_model_ids() -> list[str]:
    """Primary + fallbacks (max two fallbacks), no duplicates, no empty."""
    primary = settings.llm_model.strip()
    fallbacks = [m.strip() for m in settings.llm_fallback_models.split(",") if m.strip()][:2]
    seen = {primary}
    out = [primary]
    for m in fallbacks:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


class FallbackChatModel(BaseChatModel):
    """Chat model that tries primary then fallbacks on 402 / payment errors."""

    llms: list[ChatHuggingFace]
    model_ids: list[str]

    @property
    def _llm_type(self) -> str:
        return "fallback_huggingface"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        last_error: Exception | None = None
        for i, (model_id, llm) in enumerate(zip(self.model_ids, self.llms)):
            try:
                return llm._generate(
                    messages,
                    stop=stop,
                    run_manager=run_manager,
                    **kwargs,
                )
            except Exception as e:
                last_error = e
                if _is_payment_required_or_retryable(e) and i < len(self.llms) - 1:
                    logger.warning(
                        "llm_fallback",
                        tried=model_id,
                        error=str(e)[:200],
                        next=self.model_ids[i + 1],
                    )
                    continue
                raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM available")

    def _stream(self, *args, **kwargs):
        # Streaming: try first LLM only (fallback on 402 would require buffering)
        return self.llms[0]._stream(*args, **kwargs)


def get_llm() -> BaseChatModel:
    """Return a chat model with primary + up to two fallbacks on 402/quota errors."""
    model_ids = _llm_model_ids()
    llms = [_make_hf_llm(repo_id) for repo_id in model_ids]
    if len(llms) == 1:
        return llms[0]
    return FallbackChatModel(llms=llms, model_ids=model_ids)
