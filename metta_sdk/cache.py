"""Caching utilities for ElevenLabs API calls."""

import hashlib
import json
from pathlib import Path
from typing import Optional


class ElevenLabsCache:
    """File-based cache for ElevenLabs API responses."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize cache.

        Args:
            cache_dir: Directory for cache files. Defaults to metta_sdk/.cache
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / ".cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Subdirectories for different cache types
        self.voice_dir = self.cache_dir / "voices"
        self.ambiance_dir = self.cache_dir / "ambiance"
        self.music_dir = self.cache_dir / "music"

        for d in [self.voice_dir, self.ambiance_dir, self.music_dir]:
            d.mkdir(exist_ok=True)

    def _hash_key(self, *args) -> str:
        """Create a hash key from arguments."""
        key_str = json.dumps(args, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def get_voice_conversion(
        self,
        audio_hash: str,
        voice_id: str,
        culture: str,
    ) -> Optional[bytes]:
        """Get cached voice conversion.

        Args:
            audio_hash: Hash of input audio
            voice_id: Voice ID used
            culture: Culture name

        Returns:
            Cached audio bytes or None
        """
        key = self._hash_key(audio_hash, voice_id, culture)
        cache_file = self.voice_dir / f"{key}.wav"

        if cache_file.exists():
            print(f"    [CACHE HIT] voice conversion: {culture}")
            return cache_file.read_bytes()
        return None

    def set_voice_conversion(
        self,
        audio_hash: str,
        voice_id: str,
        culture: str,
        audio_bytes: bytes,
    ) -> None:
        """Cache voice conversion result.

        Args:
            audio_hash: Hash of input audio
            voice_id: Voice ID used
            culture: Culture name
            audio_bytes: Converted audio bytes
        """
        key = self._hash_key(audio_hash, voice_id, culture)
        cache_file = self.voice_dir / f"{key}.wav"
        cache_file.write_bytes(audio_bytes)

    def get_ambiance(
        self,
        culture: str,
        duration_seconds: float = None,  # Ignored - we cache by culture only
    ) -> Optional[bytes]:
        """Get cached ambiance.

        Ambiance is cached by culture only (not duration) - loops are handled
        by the caller to fill needed duration.

        Args:
            culture: Culture name
            duration_seconds: Ignored (kept for API compatibility)

        Returns:
            Cached audio bytes or None
        """
        # Cache by culture only - the caller will loop to fill duration
        cache_file = self.ambiance_dir / f"{culture}.wav"

        if cache_file.exists():
            print(f"    [CACHE HIT] ambiance: {culture}")
            return cache_file.read_bytes()
        return None

    def set_ambiance(
        self,
        culture: str,
        duration_seconds: float = None,  # Ignored
        audio_bytes: bytes = None,
    ) -> None:
        """Cache ambiance result.

        Ambiance is cached by culture only.

        Args:
            culture: Culture name
            duration_seconds: Ignored
            audio_bytes: Ambiance audio bytes
        """
        cache_file = self.ambiance_dir / f"{culture}.wav"
        cache_file.write_bytes(audio_bytes)

    def get_music(
        self,
        prompt: str,
        duration_ms: int,
    ) -> Optional[bytes]:
        """Get cached music.

        Args:
            prompt: Music generation prompt
            duration_ms: Duration in milliseconds

        Returns:
            Cached audio bytes or None
        """
        key = self._hash_key(prompt, duration_ms)
        cache_file = self.music_dir / f"{key}.wav"

        if cache_file.exists():
            print("[CACHE HIT] music generation")
            return cache_file.read_bytes()
        return None

    def set_music(
        self,
        prompt: str,
        duration_ms: int,
        audio_bytes: bytes,
    ) -> None:
        """Cache music result.

        Args:
            prompt: Music generation prompt
            duration_ms: Duration in milliseconds
            audio_bytes: Music audio bytes
        """
        key = self._hash_key(prompt, duration_ms)
        cache_file = self.music_dir / f"{key}.wav"
        cache_file.write_bytes(audio_bytes)

    def hash_audio(self, audio_bytes: bytes) -> str:
        """Create hash of audio bytes for cache key."""
        return hashlib.md5(audio_bytes).hexdigest()[:16]

    def clear(self) -> None:
        """Clear all cached files."""
        import shutil

        for d in [self.voice_dir, self.ambiance_dir, self.music_dir]:
            shutil.rmtree(d)
            d.mkdir(exist_ok=True)
        print("Cache cleared.")
