#!/usr/bin/env python
"""Generate a cross-cultural metta meditation from the plan."""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

from metta_sdk.generator import MettaGenerator
from metta_sdk.plan import MettaPlan


def mix_with_music(
    voice_audio: np.ndarray,
    music_path: str,
    voice_sr: int,
    music_volume_start: float = 0.10,
    music_volume_end: float = 0.85,
) -> np.ndarray:
    """Mix voice audio with background music, ramping volume throughout.

    The music starts quiet and builds to become dominant by the end.

    Args:
        voice_audio: Voice/meditation audio array
        music_path: Path to background music file
        voice_sr: Sample rate of voice audio
        music_volume_start: Music volume at start (0-1)
        music_volume_end: Music volume at end (0-1)

    Returns:
        Mixed audio array
    """
    # Load music
    music, music_sr = sf.read(music_path)
    if music.ndim > 1:
        music = np.mean(music, axis=1)
    music = music.astype(np.float32)

    # Resample music if needed
    if music_sr != voice_sr:
        import librosa

        music = librosa.resample(music, orig_sr=music_sr, target_sr=voice_sr)

    # Extend or trim music to match voice length
    if len(music) < len(voice_audio):
        # Loop music
        repeats = int(np.ceil(len(voice_audio) / len(music)))
        music = np.tile(music, repeats)
    music = music[: len(voice_audio)]

    # Apply volume ramp to music (starts quiet, ends loud)
    volume_ramp = np.linspace(music_volume_start, music_volume_end, len(music))
    music = music * volume_ramp

    # Also fade down the voice slightly toward the end so music dominates
    voice_fade = np.ones(len(voice_audio))
    fade_start = int(len(voice_audio) * 0.7)  # Start fading voice at 70%
    fade_length = len(voice_audio) - fade_start
    voice_fade[fade_start:] = np.linspace(1.0, 0.6, fade_length)
    voice_audio = voice_audio * voice_fade

    # Mix
    mixed = voice_audio + music

    # Normalize
    max_val = np.max(np.abs(mixed))
    if max_val > 0.95:
        mixed = mixed / max_val * 0.95

    return mixed.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Generate metta meditation")
    parser.add_argument(
        "--no-music",
        action="store_true",
        help="Skip background music mixing",
    )
    parser.add_argument(
        "--music-volume-start",
        type=float,
        default=0.10,
        help="Music volume at start (0-1, default: 0.10)",
    )
    parser.add_argument(
        "--music-volume-end",
        type=float,
        default=0.85,
        help="Music volume at end (0-1, default: 0.85)",
    )
    args = parser.parse_args()

    # Paths
    base_dir = Path(__file__).parent
    plan_path = base_dir / "plan.json"
    segments_dir = base_dir / "segments"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    music_path = output_dir / "meditation_music.wav"
    output_path = output_dir / "world_voices_meditation.wav"

    # Load plan
    plan = MettaPlan.load(str(plan_path))
    print(f"Loaded plan: {plan.name}")
    print(f"Description: {plan.description}")

    # Generate voices
    generator = MettaGenerator()
    result = generator.generate_from_plan(
        segments_dir=str(segments_dir),
        plan=plan,
        output_path=None,  # Don't save yet
    )

    # Mix with music if available and not skipped
    if not args.no_music and music_path.exists():
        print(
            f"\nMixing with background music (volume: {args.music_volume_start} -> {args.music_volume_end})..."
        )
        final_audio = mix_with_music(
            result.audio,
            str(music_path),
            result.sample_rate,
            music_volume_start=args.music_volume_start,
            music_volume_end=args.music_volume_end,
        )
    else:
        if not args.no_music and not music_path.exists():
            print(f"\nNo music file found at {music_path}")
            print("Run 'uv run python metta_sdk/generate_music.py' to generate it")
        final_audio = result.audio

    # Save final output
    sf.write(str(output_path), final_audio, result.sample_rate)
    duration = len(final_audio) / result.sample_rate

    print(f"\nComplete! Duration: {duration:.1f}s")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
