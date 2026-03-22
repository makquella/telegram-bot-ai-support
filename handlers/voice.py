"""Voice message handler — STT → LLM → TTS pipeline."""

import os
import uuid
import structlog
from aiogram import Router, F, types
from aiogram.types import FSInputFile

from utils.audio import convert_ogg_to_wav, transcribe_audio, generate_speech
from utils.llm import generate_response
from memory.conversation import memory

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
    """Handle voice messages: transcribe → generate response → synthesize.

    Pipeline:
    1. Download OGG voice from Telegram
    2. Convert OGG → WAV
    3. Transcribe WAV → text (faster-whisper)
    4. Send transcription to user
    5. Generate LLM response
    6. Synthesize response → audio (edge-tts)
    7. Send voice + text reply
    """
    user_id = message.from_user.id
    msg = await message.answer("🎙️ Обрабатываю голосовое...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")

    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    base_id = str(uuid.uuid4())
    ogg_path = os.path.join(data_dir, f"{base_id}.ogg")
    wav_path = os.path.join(data_dir, f"{base_id}.wav")
    tts_path = os.path.join(data_dir, f"{base_id}_response.mp3")

    try:
        await message.bot.download(message.voice, destination=ogg_path)

        if not await convert_ogg_to_wav(ogg_path, wav_path):
            await _safe_delete(msg)
            await message.answer("❌ Не удалось обработать аудио. Убедитесь что ffmpeg установлен.")
            return

        user_text = await transcribe_audio(wav_path)
        if not user_text:
            await _safe_delete(msg)
            await message.answer("❌ Не удалось распознать речь.")
            return

        # Show transcription
        await _safe_delete(msg)
        await message.answer(f"🗣 Вы сказали: {user_text}")

        await memory.add_message(user_id, "user", user_text)
        messages = await memory.get_messages(user_id)

        llm_response = await generate_response(messages)
        await memory.add_message(user_id, "assistant", llm_response)

        # Generate and send voice response
        if await generate_speech(llm_response, tts_path):
            voice_file = FSInputFile(tts_path)
            await message.answer_voice(voice=voice_file)

        # Always send text version
        await message.answer(llm_response)

    except Exception as e:
        logger.error("Voice handler failed", error=str(e))
        await _safe_delete(msg)
        await message.answer("❌ Ошибка при обработке голосового сообщения.")
    finally:
        for path in [ogg_path, wav_path, tts_path]:
            if os.path.exists(path):
                os.remove(path)
