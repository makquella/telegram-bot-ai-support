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

@router.message(F.voice)
async def handle_voice(message: types.Message):
    user_id = message.from_user.id
    msg = await message.answer("🎙️ Processing voice message...")
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
            await msg.edit_text("❌ Failed to process audio format. Please ensure ffmpeg is installed.")
            return
            
        user_text = await transcribe_audio(wav_path)
        if not user_text:
            await msg.edit_text("❌ Could not understand the audio.")
            return
            
        await memory.add_message(user_id, "user", user_text)
        messages = await memory.get_messages(user_id)
        
        llm_response = await generate_response(messages)
        await memory.add_message(user_id, "assistant", llm_response)
        
        success = await generate_speech(llm_response, tts_path)
        
        if success:
            await msg.delete()
            voice_file = FSInputFile(tts_path)
            await message.answer_voice(voice=voice_file, caption=llm_response)
        else:
            await msg.edit_text(llm_response)

    except Exception as e:
        logger.error("Voice Handler Error", error=str(e))
        await msg.edit_text("❌ An error occurred while processing voice.")
    finally:
        for path in [ogg_path, wav_path, tts_path]:
            if os.path.exists(path):
                os.remove(path)
