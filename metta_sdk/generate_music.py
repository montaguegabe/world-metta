#!/usr/bin/env python
"""Generate meditation background music with volume ramp."""

import io
import os
from pathlib import Path

import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from metta_sdk.cache import ElevenLabsCache

# Music prompt - used for both generation and cache key
MUSIC_PROMPT = (
    "Deep meditation music with gravitas and emotional depth. "
    "Slow evolving ambient pads, low resonant drones, gentle bells, "
    "peaceful but profound atmosphere. Builds slowly in richness and power. "
    "Sacred, contemplative, with a sense of expanding consciousness."
)


def generate_meditation_music(
    duration_minutes: float = 4.0,
    output_path: str = None,
) -> str:
    """Generate meditation music that builds in intensity.

    Args:
        duration_minutes: Length of music in minutes
        output_path: Where to save the music

    Returns:
        Path to saved music file
    """
    load_dotenv()
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    cache = ElevenLabsCache()

    # Output path
    if output_path is None:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / "meditation_music.wav")

    duration_ms = int(duration_minutes * 60 * 1000)

    print(f"Generating {duration_minutes} minutes of meditation music...")
    print("Prompt: Deep meditation music, relaxing but with gravitas and depth")

    # Check cache first
    cached = cache.get_music(MUSIC_PROMPT, duration_ms)
    if cached is not None:
        audio_bytes = cached
    else:
        # Generate music
        result = client.music.compose(
            prompt=MUSIC_PROMPT,
            music_length_ms=duration_ms,
            model_id="music_v1",
            force_instrumental=True,
        )

        print("Downloading music...")
        audio_bytes = b"".join(chunk for chunk in result)

        # Cache the result
        cache.set_music(MUSIC_PROMPT, duration_ms, audio_bytes)

    # Load audio
    audio, sr = sf.read(io.BytesIO(audio_bytes))
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)  # Convert to mono
    audio = audio.astype(np.float32)

    print(f"Generated {len(audio) / sr:.1f}s of audio at {sr}Hz")

    # Apply volume ramp: start at 30% volume, end at 100%
    print("Applying volume ramp (30% -> 100%)...")
    volume_ramp = np.linspace(0.3, 1.0, len(audio))
    audio = audio * volume_ramp

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0.95:
        audio = audio / max_val * 0.95

    # Save
    sf.write(output_path, audio, sr)
    print(f"Saved to: {output_path}")

    return output_path


if __name__ == "__main__":
    generate_meditation_music()
