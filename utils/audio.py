import os
import asyncio
import structlog
from faster_whisper import WhisperModel
import edge_tts
from pydub import AudioSegment

logger = structlog.get_logger(__name__)

# Initialize whisper model once.
try:
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
except Exception as e:
    logger.error("Failed to load whisper model", error=str(e))
    whisper_model = None

async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using faster-whisper."""
    if not whisper_model:
        return "Sorry, speech-to-text is currently unavailable."
    
    try:
        loop = asyncio.get_running_loop()
        def transcribe():
            segments, info = whisper_model.transcribe(audio_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text
        
        text = await loop.run_in_executor(None, transcribe)
        return text.strip()
    except Exception as e:
        logger.error("Transcription Error", error=str(e))
        return ""

async def generate_speech(text: str, output_path: str) -> bool:
    """Generate speech using async edge-tts."""
    try:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error("TTS Error", error=str(e))
        return False

async def convert_ogg_to_wav(input_path: str, output_path: str) -> bool:
    """Convert Telegram OGG voice to WAV for Whisper using pydub."""
    try:
        loop = asyncio.get_running_loop()
        def convert():
            audio = AudioSegment.from_ogg(input_path)
            audio.export(output_path, format="wav")
        await loop.run_in_executor(None, convert)
        return True
    except Exception as e:
        logger.error("Audio Conversion Error", error=str(e))
        return False
