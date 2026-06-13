import io
import wave
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TTSProvider:
    """Abstract base class for Text-to-Speech providers."""
    def generate(self, text: str, voice: str) -> bytes:
        raise NotImplementedError("Subclasses must implement generate()")

class KittenTTSProvider(TTSProvider):
    """Kitten TTS provider using the local KittenTTS model."""
    def __init__(self, model_name: str = "KittenML/kitten-tts-nano-0.8"):
        logger.info(f"Initializing KittenTTSProvider with model: {model_name}")
        try:
            from kittentts import KittenTTS
            self.model = KittenTTS(model_name)
            self.enabled = True
            logger.info("KittenTTS loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize KittenTTS: {e}. Falling back to mock TTS.", exc_info=True)
            self.enabled = False

    def generate(self, text: str, voice: str = "Jasper") -> bytes:
        if not self.enabled:
            # Return empty/mock bytes or raise error
            raise RuntimeError("KittenTTS is not enabled.")
        
        # Kitten TTS generate returns a numpy float32 array
        # Clip/scale and convert to int16 mono 24kHz WAV
        logger.info(f"Generating TTS audio for text: '{text}' using voice '{voice}'")
        audio = self.model.generate(text, voice=voice)
        
        # Audio clipping and conversion
        audio_int16 = (audio * 32767.0).clip(-32768, 32767).astype(np.int16)
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)       # Mono
            wav_file.setsampwidth(2)       # 16-bit
            wav_file.setframerate(24000)   # 24kHz sample rate
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_io.getvalue()
