"""Voice message handler — STT → RAG → LLM → TTS pipeline."""

import uuid
from pathlib import Path

import structlog
from aiogram import Router, F, types
from aiogram.types import FSInputFile

from config import config
from memory.conversation import memory
from services.conversation import build_inference_messages, build_user_message_content
from utils.audio import convert_ogg_to_wav, transcribe_audio, generate_speech
from utils.llm import generate_response

logger = structlog.get_logger(__name__)
router = Router(name="voice")


async def _safe_delete(msg: types.Message) -> None:
    """Delete a message ignoring errors (e.g. already deleted)."""
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.voice)
async def handle_voice(message: types.Message) -> None:
    """Handle voice messages: transcribe → retrieve context → respond → synthesize.

    Pipeline:
    1. Download OGG voice from Telegram
    2. Convert OGG → WAV
    3. Transcribe WAV → text (faster-whisper)
    4. Retrieve relevant document context (optional, configurable)
    5. Generate LLM response
    6. Persist raw user/assistant messages in chat memory
    7. Synthesize response → audio (edge-tts)
    8. Send voice + text reply
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    msg = await message.answer("🎙️ Обрабатываю голосовое...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")

    config.data_dir.mkdir(parents=True, exist_ok=True)

    base_id = str(uuid.uuid4())
    ogg_path = config.data_dir / f"{base_id}.ogg"
    wav_path = config.data_dir / f"{base_id}.wav"
    tts_path = config.data_dir / f"{base_id}_response.mp3"

    try:
        await message.bot.download(message.voice, destination=str(ogg_path))

        if not await convert_ogg_to_wav(str(ogg_path), str(wav_path)):
            await _safe_delete(msg)
            await message.answer("❌ Не удалось обработать аудио. Убедитесь что ffmpeg установлен.")
            return

        user_text = await transcribe_audio(str(wav_path))
        if not user_text:
            await _safe_delete(msg)
            await message.answer("❌ Не удалось распознать речь.")
            return

        # Show transcription
        await _safe_delete(msg)
        await message.answer(f"🗣 Вы сказали: {user_text}")

        history_messages = await memory.get_messages(user_id, chat_id)
        user_content = await build_user_message_content(
            user_text,
            user_id=user_id,
            chat_id=chat_id,
            use_rag=config.voice_use_rag,
        )
        messages = build_inference_messages(history_messages, user_content)

        llm_response = await generate_response(messages)
        await memory.add_message(user_id, chat_id, "user", user_text)
        await memory.add_message(user_id, chat_id, "assistant", llm_response)

        # Try to send a voice reply when the chat allows it.
        if await generate_speech(llm_response, str(tts_path)):
            try:
                voice_file = FSInputFile(str(tts_path))
                await message.answer_voice(voice=voice_file)
            except Exception as e:
                logger.warning(
                    "Voice reply delivery failed",
                    error=str(e),
                    user_id=user_id,
                    chat_id=chat_id,
                )

        # Always send text version
        await message.answer(llm_response)

    except Exception as e:
        logger.error("Voice handler failed", error=str(e))
        await _safe_delete(msg)
        await message.answer("❌ Ошибка при обработке голосового сообщения.")
    finally:
        for path in [ogg_path, wav_path, tts_path]:
            if path.exists():
                path.unlink()
