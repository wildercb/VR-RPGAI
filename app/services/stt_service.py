"""Speech-to-Text service using Faster-Whisper via Wyoming protocol."""
import asyncio
import io
import wave
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger
from wyoming.client import AsyncClient
from wyoming.asr import Transcribe
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.info import Describe, Info
from app.config import settings


class STTService:
    """Local STT service using Faster-Whisper via Wyoming protocol."""

    def __init__(self):
        """Initialize STT service with Whisper configuration."""
        self.whisper_url = settings.WHISPER_STT_URL
        # Parse host and port from URL
        url_parts = self.whisper_url.replace("http://", "").split(":")
        self.whisper_host = url_parts[0]
        self.whisper_port = int(url_parts[1]) if len(url_parts) > 1 else 10300

        logger.info(f"STT Service initialized with Whisper at {self.whisper_url}")

    async def transcribe(self, audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
        """
        Transcribe audio to text using Faster-Whisper via Wyoming protocol.

        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            audio_format: Audio format (default: "wav")

        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            logger.info(f"Transcribing audio via Wyoming at {self.whisper_host}:{self.whisper_port}")

            # Parse WAV file to get audio parameters
            audio_info = self._parse_audio_info(audio_data, audio_format)
            if not audio_info:
                logger.error("Failed to parse audio info")
                return None

            sample_rate, sample_width, channels, audio_bytes = audio_info

            # Connect to Wyoming server
            wyoming_uri = f"tcp://{self.whisper_host}:{self.whisper_port}"
            async with AsyncClient.from_uri(wyoming_uri) as client:
                # Send transcription request
                transcribe_request = Transcribe(language=settings.WHISPER_LANGUAGE).event()
                await client.write_event(transcribe_request)

                # Send audio start event
                audio_start = AudioStart(
                    rate=sample_rate,
                    width=sample_width,
                    channels=channels
                ).event()
                await client.write_event(audio_start)

                # Send audio in chunks (Wyoming protocol uses 1024-byte chunks)
                chunk_size = 1024
                for i in range(0, len(audio_bytes), chunk_size):
                    chunk_data = audio_bytes[i:i + chunk_size]
                    audio_chunk = AudioChunk(
                        rate=sample_rate,
                        width=sample_width,
                        channels=channels,
                        audio=chunk_data
                    ).event()
                    await client.write_event(audio_chunk)

                # Send audio stop event
                audio_stop = AudioStop().event()
                await client.write_event(audio_stop)

                # Receive transcription result
                while True:
                    event = await client.read_event()

                    if event is None:
                        logger.warning("Connection closed before receiving transcript")
                        return None

                    if event.type == "transcript":
                        transcript_text = event.data.get("text", "")
                        logger.info(f"Transcription complete: {len(transcript_text)} chars")
                        logger.debug(f"Transcript: {transcript_text}")
                        return transcript_text

                    elif event.type == "error":
                        error_msg = event.data.get("text", "Unknown error")
                        logger.error(f"Transcription error: {error_msg}")
                        return None

        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            return None

    def _parse_audio_info(self, audio_data: bytes, audio_format: str) -> Optional[tuple]:
        """
        Parse audio file to extract parameters.
        Uses FFmpeg to convert any audio format to 16kHz mono WAV.

        Returns:
            Tuple of (sample_rate, sample_width, channels, raw_audio_bytes) or None
        """
        try:
            # Try to parse as WAV first
            if audio_data[:4] == b'RIFF':
                try:
                    with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                        sample_rate = wav_file.getframerate()
                        sample_width = wav_file.getsampwidth()
                        channels = wav_file.getnchannels()
                        audio_bytes = wav_file.readframes(wav_file.getnframes())

                        logger.debug(
                            f"Audio info (WAV): {sample_rate}Hz, {sample_width} bytes, "
                            f"{channels} channels, {len(audio_bytes)} bytes"
                        )

                        return (sample_rate, sample_width, channels, audio_bytes)
                except Exception as wav_error:
                    logger.warning(f"WAV parsing failed, trying FFmpeg conversion: {wav_error}")

            # Use FFmpeg to convert to 16kHz mono WAV
            logger.info(f"Converting {audio_format} audio to WAV using FFmpeg")

            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
                output_path = output_file.name

            try:
                # Convert to 16kHz, mono, 16-bit PCM WAV using FFmpeg
                subprocess.run([
                    'ffmpeg',
                    '-i', input_path,
                    '-ar', '16000',  # Sample rate: 16kHz
                    '-ac', '1',      # Channels: mono
                    '-sample_fmt', 's16',  # 16-bit PCM
                    '-f', 'wav',
                    '-y',  # Overwrite output
                    output_path
                ], check=True, capture_output=True)

                # Read converted WAV file
                with open(output_path, 'rb') as f:
                    converted_data = f.read()

                # Parse the converted WAV
                with wave.open(io.BytesIO(converted_data), 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    sample_width = wav_file.getsampwidth()
                    channels = wav_file.getnchannels()
                    audio_bytes = wav_file.readframes(wav_file.getnframes())

                    logger.info(
                        f"Audio converted: {sample_rate}Hz, {sample_width} bytes, "
                        f"{channels} channels, {len(audio_bytes)} bytes"
                    )

                    return (sample_rate, sample_width, channels, audio_bytes)

            finally:
                # Cleanup temp files
                Path(input_path).unlink(missing_ok=True)
                Path(output_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Failed to parse/convert audio: {e}")
            return None

    async def health_check(self) -> bool:
        """
        Check if Whisper STT service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            wyoming_uri = f"tcp://{self.whisper_host}:{self.whisper_port}"
            async with AsyncClient.from_uri(wyoming_uri) as client:
                # Request service info
                describe_request = Describe().event()
                await client.write_event(describe_request)

                # Wait for info response
                event = await asyncio.wait_for(client.read_event(), timeout=5.0)

                if event and event.type == "info":
                    logger.info("Whisper STT health check passed")
                    return True

                return False

        except Exception as e:
            logger.error(f"Whisper STT health check failed: {e}")
            return False


# Global STT service instance
stt_service = STTService() if settings.STT_ENABLED else None
