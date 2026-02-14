"""Audio mixing and crossfading utilities for metta meditations."""

import io
from dataclasses import dataclass
from typing import Optional

import numpy as np
import soundfile as sf


@dataclass
class SegmentTiming:
    """Timing information for a meditation segment."""

    start_sec: float
    end_sec: float
    phrase: str = ""

    @property
    def duration_sec(self) -> float:
        """Get segment duration in seconds."""
        return self.end_sec - self.start_sec


class AudioMixer:
    """Handles audio mixing, crossfading, and segment assembly."""

    def __init__(self, sample_rate: int = 44100):
        """Initialize mixer with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate

    def load_audio(self, audio_data: bytes) -> tuple[np.ndarray, int]:
        """Load audio from bytes.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Tuple of (audio array, sample rate)
        """
        audio, sr = sf.read(io.BytesIO(audio_data))

        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        return audio.astype(np.float32), sr

    def load_audio_file(self, path: str) -> tuple[np.ndarray, int]:
        """Load audio from file.

        Args:
            path: Path to audio file

        Returns:
            Tuple of (audio array, sample rate)
        """
        audio, sr = sf.read(path)

        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        return audio.astype(np.float32), sr

    def extract_segment(
        self,
        audio: np.ndarray,
        start_sec: float,
        end_sec: float,
    ) -> np.ndarray:
        """Extract a segment from audio.

        Args:
            audio: Audio array
            start_sec: Start time in seconds
            end_sec: End time in seconds

        Returns:
            Extracted audio segment
        """
        start_sample = int(start_sec * self.sample_rate)
        end_sample = int(end_sec * self.sample_rate)

        return audio[start_sample:end_sample].copy()

    def apply_fade(
        self,
        audio: np.ndarray,
        fade_in_sec: float = 0.0,
        fade_out_sec: float = 0.0,
    ) -> np.ndarray:
        """Apply fade in and/or fade out to audio.

        Args:
            audio: Audio array
            fade_in_sec: Fade in duration in seconds
            fade_out_sec: Fade out duration in seconds

        Returns:
            Audio with fades applied
        """
        audio = audio.copy()

        fade_in_samples = int(fade_in_sec * self.sample_rate)
        fade_out_samples = int(fade_out_sec * self.sample_rate)

        # Apply fade in
        if fade_in_samples > 0:
            fade_in_samples = min(fade_in_samples, len(audio))
            fade_in = np.linspace(0, 1, fade_in_samples)
            audio[:fade_in_samples] *= fade_in

        # Apply fade out
        if fade_out_samples > 0:
            fade_out_samples = min(fade_out_samples, len(audio))
            fade_out = np.linspace(1, 0, fade_out_samples)
            audio[-fade_out_samples:] *= fade_out

        return audio

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        crossfade_sec: float,
    ) -> np.ndarray:
        """Crossfade between two audio segments.

        Args:
            audio1: First audio segment
            audio2: Second audio segment
            crossfade_sec: Crossfade duration in seconds

        Returns:
            Combined audio with crossfade
        """
        crossfade_samples = int(crossfade_sec * self.sample_rate)
        crossfade_samples = min(crossfade_samples, len(audio1), len(audio2))

        if crossfade_samples <= 0:
            return np.concatenate([audio1, audio2])

        # Create fade curves
        fade_out = np.linspace(1, 0, crossfade_samples)
        fade_in = np.linspace(0, 1, crossfade_samples)

        # Apply crossfade
        result = np.zeros(len(audio1) + len(audio2) - crossfade_samples)

        # Copy audio1 with fade out at end
        result[: len(audio1)] = audio1.copy()
        result[len(audio1) - crossfade_samples : len(audio1)] *= fade_out

        # Add audio2 with fade in at start
        audio2_faded = audio2.copy()
        audio2_faded[:crossfade_samples] *= fade_in
        result[len(audio1) - crossfade_samples :] += audio2_faded

        return result.astype(np.float32)

    def mix_with_ambiance(
        self,
        voice_audio: np.ndarray,
        ambiance_audio: np.ndarray,
        voice_volume: float = 1.0,
        ambiance_volume: float = 0.3,
        pad_before_sec: float = 2.0,
        pad_after_sec: float = 2.0,
    ) -> np.ndarray:
        """Mix voice audio with ambient background, with padding.

        Args:
            voice_audio: Voice/speech audio
            ambiance_audio: Background ambiance audio
            voice_volume: Volume multiplier for voice (0-1)
            ambiance_volume: Volume multiplier for ambiance (0-1)
            pad_before_sec: Seconds of ambiance before voice starts
            pad_after_sec: Seconds of ambiance after voice ends

        Returns:
            Mixed audio with ambiance padding
        """
        pad_before_samples = int(pad_before_sec * self.sample_rate)
        pad_after_samples = int(pad_after_sec * self.sample_rate)
        total_length = pad_before_samples + len(voice_audio) + pad_after_samples

        # Ensure ambiance is long enough
        if len(ambiance_audio) < total_length:
            repeats = int(np.ceil(total_length / len(ambiance_audio)))
            ambiance_audio = np.tile(ambiance_audio, repeats)
        ambiance_audio = ambiance_audio[:total_length].copy()

        # Create output array starting with ambiance
        mixed = ambiance_audio * ambiance_volume

        # Overlay voice in the middle (after padding)
        mixed[pad_before_samples : pad_before_samples + len(voice_audio)] += (
            voice_audio * voice_volume
        )

        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 0.95:
            mixed = mixed / max_val * 0.95

        return mixed.astype(np.float32)

    def assemble_meditation(
        self,
        segments: list[np.ndarray],
        crossfade_sec: float = 3.0,
    ) -> np.ndarray:
        """Assemble multiple segments with crossfades into final meditation.

        Args:
            segments: List of audio segments
            crossfade_sec: Crossfade duration between segments

        Returns:
            Assembled meditation audio
        """
        if not segments:
            return np.array([], dtype=np.float32)

        if len(segments) == 1:
            return segments[0]

        # Start with first segment
        result = segments[0].copy()

        # Crossfade each subsequent segment
        for segment in segments[1:]:
            result = self.crossfade(result, segment, crossfade_sec)

        return result

    def export_audio(
        self,
        audio: np.ndarray,
        path: str,
        sample_rate: Optional[int] = None,
    ) -> str:
        """Export audio to file.

        Args:
            audio: Audio array
            path: Output file path
            sample_rate: Sample rate (uses instance default if not provided)

        Returns:
            Path to saved file
        """
        sr = sample_rate or self.sample_rate
        sf.write(path, audio, sr)
        print(f"Saved: {path}")
        return path

    def audio_to_bytes(
        self,
        audio: np.ndarray,
        format: str = "wav",
        sample_rate: Optional[int] = None,
    ) -> bytes:
        """Convert audio array to bytes.

        Args:
            audio: Audio array
            format: Output format (wav, mp3, etc.)
            sample_rate: Sample rate

        Returns:
            Audio bytes
        """
        sr = sample_rate or self.sample_rate
        buffer = io.BytesIO()
        sf.write(buffer, audio, sr, format=format)
        buffer.seek(0)
        return buffer.read()
