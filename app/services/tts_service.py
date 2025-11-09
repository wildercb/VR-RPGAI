"""Text-to-Speech service using Piper TTS via Wyoming protocol."""
import asyncio
import hashlib
import os
import wave
from pathlib import Path
from typing import Optional
from loguru import logger
from wyoming.client import AsyncClient
from wyoming.tts import Synthesize
from wyoming.audio import AudioChunk


class TTSService:
    """Local TTS service using Piper TTS via Wyoming protocol."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            # Parse Wyoming URL (e.g., "http://piper:10200")
            piper_url = os.getenv('PIPER_TTS_URL', 'http://piper:10200')
            # Extract host and port
            if piper_url.startswith('http://'):
                piper_url = piper_url[7:]  # Remove 'http://'
            parts = piper_url.split(':')
            self.piper_host = parts[0]
            self.piper_port = int(parts[1]) if len(parts) > 1 else 10200

            self.cache_dir = Path(os.getenv('AUDIO_CACHE_PATH', '/app/audio_cache'))
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            logger.info(f"TTS Service initialized with Piper at {self.piper_host}:{self.piper_port}")

    def _get_cache_path(self, text: str, voice: str = "default") -> Path:
        """Generate cache file path based on text and voice."""
        cache_key = hashlib.md5(f"{voice}:{text}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.wav"

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Synthesize speech from text using Piper TTS via Wyoming protocol.

        Args:
            text: Text to synthesize
            voice: Voice ID (optional)
            use_cache: Whether to use cached audio

        Returns:
            Path to generated WAV file, or None if synthesis failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return None

        # Check cache first
        cache_path = self._get_cache_path(text, voice or "default")
        if use_cache and cache_path.exists():
            logger.debug(f"Using cached TTS audio: {cache_path}")
            return str(cache_path)

        try:
            logger.info(f"Synthesizing TTS via Wyoming at {self.piper_host}:{self.piper_port}")

            # Connect to Wyoming server
            wyoming_uri = f"tcp://{self.piper_host}:{self.piper_port}"
            async with AsyncClient.from_uri(wyoming_uri) as client:
                # Send synthesis request
                # Note: Voice selection is done at Piper server startup, not per-request
                synth_request = Synthesize(text=text)
                await client.write_event(synth_request.event())

                # Receive audio chunks
                audio_data = bytearray()
                sample_rate = 16000  # Default for Piper
                sample_width = 2  # 16-bit
                channels = 1  # Mono

                while True:
                    event = await client.read_event()

                    if event is None:
                        logger.error("Connection closed by server")
                        return None

                    if event.type == "audio-stop":
                        logger.debug("Audio synthesis complete")
                        break

                    if event.type == "audio-start":
                        # Extract audio parameters if available
                        if hasattr(event, 'rate'):
                            sample_rate = event.rate
                        if hasattr(event, 'width'):
                            sample_width = event.width
                        if hasattr(event, 'channels'):
                            channels = event.channels
                        logger.debug(f"Audio start: {sample_rate}Hz, {sample_width} bytes, {channels} channels")

                    elif event.type == "audio-chunk":
                        chunk = AudioChunk.from_event(event)
                        audio_data.extend(chunk.audio)

                if not audio_data:
                    logger.error("No audio data received from Piper")
                    return None

                # Write to WAV file
                with wave.open(str(cache_path), 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(bytes(audio_data))

                logger.info(f"Generated TTS audio: {len(text)} chars -> {len(audio_data)} bytes -> {cache_path}")
                return str(cache_path)

        except ConnectionRefusedError as e:
            logger.error(f"Cannot connect to Piper at {self.piper_host}:{self.piper_port}: {e}")
            return None
        except asyncio.TimeoutError as e:
            logger.error(f"Piper TTS timeout: {e}")
            return None
        except Exception as e:
            logger.error(f"TTS synthesis error: {type(e).__name__}: {e}", exc_info=True)
            return None

    async def health_check(self) -> bool:
        """Check if TTS service is available."""
        try:
            wyoming_uri = f"tcp://{self.piper_host}:{self.piper_port}"
            # Try to connect with a short timeout
            async with asyncio.timeout(5.0):
                async with AsyncClient.from_uri(wyoming_uri) as client:
                    # If we can connect, service is healthy
                    return True
        except Exception as e:
            logger.warning(f"TTS health check failed: {e}")
            return False

    def clear_cache(self):
        """Clear all cached audio files."""
        for audio_file in self.cache_dir.glob("*.wav"):
            audio_file.unlink()
        logger.info("TTS cache cleared")


# Global singleton instance
tts_service = TTSService()
