"""Audio processing: STT (faster-whisper) and TTS (edge-tts)."""

import os
import asyncio
import structlog
from pydub import AudioSegment

from config import config

logger = structlog.get_logger(__name__)

# Lazy-loaded whisper model (downloaded on first use)
_whisper_model = None


def _get_whisper_model():
    """Lazy-load the Whisper model to avoid slow startup."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper model",
            model=config.whisper_model,
            device=config.whisper_device,
        )
        _whisper_model = WhisperModel(
            config.whisper_model,
            device=config.whisper_device,
            compute_type=config.whisper_compute,
        )
    return _whisper_model


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file to text using faster-whisper.

    Args:
        audio_path: Path to the WAV audio file.

    Returns:
        Transcribed text or empty string on failure.
    """
    try:
        model = _get_whisper_model()
        loop = asyncio.get_running_loop()

        def _transcribe():
            segments, info = model.transcribe(
                audio_path,
                beam_size=5,
                language="ru",
            )
            return " ".join(seg.text for seg in segments)

        text = await loop.run_in_executor(None, _transcribe)
        return text.strip()
    except Exception as e:
        logger.error("Transcription failed", error=str(e))
        return ""


async def generate_speech(text: str, output_path: str) -> bool:
    """Generate speech audio from text using Edge-TTS.

    Args:
        text: Text to synthesize.
        output_path: Path to save the generated audio file.

    Returns:
        True on success, False on failure.
    """
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, config.tts_voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error("TTS generation failed", error=str(e))
        return False


async def convert_ogg_to_wav(input_path: str, output_path: str) -> bool:
    """Convert Telegram OGG voice message to WAV for Whisper.

    Args:
        input_path: Path to the OGG file.
        output_path: Path to save the WAV file.

    Returns:
        True on success, False on failure.
    """
    try:
        loop = asyncio.get_running_loop()

        def _convert():
            audio = AudioSegment.from_ogg(input_path)
            audio.export(output_path, format="wav")

        await loop.run_in_executor(None, _convert)
        return True
    except Exception as e:
        logger.error("Audio conversion failed", error=str(e))
        return False
