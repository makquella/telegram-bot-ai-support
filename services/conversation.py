"""Shared helpers for preparing conversation turns for the LLM."""

from collections.abc import Awaitable, Callable

import structlog

from rag.chain import retrieve_context

logger = structlog.get_logger(__name__)

Retriever = Callable[[str, int, int], Awaitable[str]]


async def build_user_message_content(
    user_text: str,
    user_id: int,
    chat_id: int,
    use_rag: bool = True,
    retriever: Retriever = retrieve_context,
) -> str:
    """Return user content augmented with document context when available."""
    if not use_rag:
        return user_text

    try:
        context = await retriever(user_text, user_id, chat_id)
    except Exception as e:
        logger.warning(
            "RAG retrieval failed",
            error=str(e),
            user_id=user_id,
            chat_id=chat_id,
            query=user_text,
        )
        return user_text

    if not context:
        return user_text

    return f"Контекст из документов:\n{context}\n\nВопрос пользователя: {user_text}"


def build_inference_messages(
    history_messages: list[dict[str, str]],
    current_user_content: str,
) -> list[dict[str, str]]:
    """Build the LLM input without persisting RAG context in long-term memory."""
    return [*history_messages, {"role": "user", "content": current_user_content}]
