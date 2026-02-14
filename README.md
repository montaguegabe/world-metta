# World Metta

A cross-cultural metta (loving-kindness) meditation that transforms a single voice recording into a journey through diverse cultural voices and ambient soundscapes.

## The Meditation

**Listen to the generated meditation:** [`metta_sdk/output/world_voices_meditation.wav`](metta_sdk/output/world_voices_meditation.wav)

Duration: ~5.5 minutes

The meditation progresses through:
1. **Original voice** - Personal metta phrases ("May I...", "May you...")
2. **Japanese** - With zen garden ambiance
3. **Indian** - With temple bells and sitar
4. **Arabic** - With desert oasis sounds
5. **British** - With English countryside ambiance
6. **Chinese** - With traditional garden atmosphere
7. **Celtic** - With Irish countryside sounds
8. **Australian** - With outback ambiance

Features:
- Alternating male/female voices
- Progressive gaps between phrases (longer pauses as meditation deepens)
- Overlapping ambient soundscapes that crossfade into each other
- Background music that builds from subtle to prominent
- 30-second contemplative ending

## How It Works

The system uses ElevenLabs APIs to:
1. Convert speech to different cultural voices (speech-to-speech)
2. Generate culturally-appropriate ambient sounds
3. Generate meditation background music

All API responses are cached locally to enable rapid iteration without repeated API calls.

## Setup

```bash
uv sync
cp .env.example .env  # Add your ELEVENLABS_API_KEY
```

## Regenerating the Meditation

To regenerate with the same plan:

```bash
# Generate background music (cached after first run)
uv run python metta_sdk/generate_music.py

# Generate the full meditation
uv run python metta_sdk/generate.py
```

## Customization

Edit `metta_sdk/plan.json` to customize:
- Voice/culture assignments per section
- Gap timing between phrases
- Ambiance overlap duration
- Music volume progression

## Project Structure

```
metta_sdk/
  plan.json          # Meditation structure definition
  generate.py        # Main generation script
  generate_music.py  # Background music generator
  generator.py       # Core orchestration logic
  voices.py          # Cultural voice mappings
  mixer.py           # Audio mixing utilities
  cache.py           # API response caching
  output/            # Generated meditation files
```

## License

MIT License - Built for the Deep Listening Mindful Makers Hack
