# World Metta Generator

This is experimental and the resulting meditation generated still is a work in progress.

# Deep Listening Music SDK

A mindfulness-focused audio SDK for the **Deep Listening Mindful Makers Hack**. This collection of five mini-SDKs provides tools for meditation, emotional engagement with music, and mindful listening experiences.

## What is Deep Listening?

Deep Listening is a practice developed by composer Pauline Oliveros that involves listening with intention and awareness.

This SDK brings Deep Listening principles to developers through:

- **Audio Analysis** - Understanding the meditative qualities of sound
- **Sound Discovery** - Finding the perfect ambient textures
- **Therapeutic Tones** - Generating binaural beats and isochronic tones
- **Voice Journaling** - Recording reflections and soundscapes
- **AI Generation** - Creating custom meditation music

## Installation

```bash
cd mindful-makers-deep-listening-sdk
uv sync
cp .env.example .env  # Add your API keys
```

## Mini-SDKs

### 1. Librosa SDK - Audio Analysis for Mindfulness

Analyze audio to understand its meditative qualities.

See [librosa_sdk/README.md](librosa_sdk/README.md) for full documentation.

### 2. Freesound SDK - Discover Meditation Sounds

Search and download CC-licensed sounds for meditation.

**Requires:** Freesound API key (free at [freesound.org/apiv2/apply](https://freesound.org/apiv2/apply))

See [freesound_sdk/README.md](freesound_sdk/README.md) for full documentation.

### 3. WebAudio SDK - Therapeutic Tone Generation

Generate binaural beats and isochronic tones for meditation.

See [webaudio_sdk/README.md](webaudio_sdk/README.md) for full documentation.

### 4. Recording SDK - Voice Journaling

Capture audio for journaling and soundscape creation.

See [recording_sdk/README.md](recording_sdk/README.md) for full documentation.

### 5. ElevenLabs SDK - AI Meditation Music

Generate custom meditation music and nature sounds.

**Requires:** ElevenLabs API key

See [elevenlabs_sdk/README.md](elevenlabs_sdk/README.md) for full documentation.

## Quick Start Examples

Run any example to see the SDK in action:

```bash
# Analyze audio (no API key needed)
uv run python librosa_sdk/example.py

# Generate binaural beats (no API key needed)
uv run python webaudio_sdk/example.py

# Record audio (no API key needed, requires microphone)
uv run python recording_sdk/example.py

# Search meditation sounds (requires Freesound API key)
uv run python freesound_sdk/example.py

# Generate AI music (requires ElevenLabs API key)
uv run python elevenlabs_sdk/example.py
```

## License

MIT License - Built for the Deep Listening Mindful Makers Hack
