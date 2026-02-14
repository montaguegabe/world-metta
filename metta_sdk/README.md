# Metta SDK - Cross-Cultural Meditation Voice Generation

Generate culturally diverse metta meditations by transforming your voice through different cultural accents with matching ambient soundscapes.

## Overview

The Metta SDK takes your original metta meditation recording and:
1. Detects phrase boundaries (or uses manual timings)
2. Transforms your voice using ElevenLabs speech-to-speech conversion
3. Generates culturally-appropriate ambient sounds
4. Crossfades between cultures for a seamless meditation experience

## Recording Instructions

Record yourself speaking the three metta phrases clearly with brief pauses between them:

1. **"May you be happy"** (pause 1-2 seconds)
2. **"May you be peaceful"** (pause 1-2 seconds)
3. **"May you feel that you belong"**

Save the recording as `metta_sdk/input/metta.wav` (or any audio format).

### Recording Tips
- Use a quiet environment
- Speak slowly and clearly
- Leave 1-2 seconds of silence between phrases
- Recording length: 15-30 seconds total

## Quick Start

```python
from metta_sdk import MettaGenerator

# Initialize
generator = MettaGenerator()

# Generate meditation with all cultures
result = generator.generate(
    input_audio_path="input/metta.wav",
    cultures=["japanese", "indian", "african", "latin", "celtic"],
    crossfade_ms=3000,
)

# Save output
result.save("output/cultural_metta.wav")
```

## Available Cultures

| Culture | Voice Accent | Ambient Sound |
|---------|--------------|---------------|
| japanese | Japanese | Zen garden, bamboo fountain |
| indian | Indian | Sitar drone, temple bells |
| african | African (English) | Savanna, distant drums |
| latin | Spanish | Rainforest, tropical birds |
| celtic | Irish | Countryside, distant flute |

## API Reference

### MettaGenerator

```python
class MettaGenerator:
    def generate(
        self,
        input_audio_path: str,
        cultures: list[str] = None,  # Default: all cultures
        segments: list[SegmentTiming] = None,  # Auto-detected if None
        crossfade_ms: int = 3000,
        ambiance_volume: float = 0.3,
        output_path: str = None,
    ) -> MettaResult:
        """Generate cross-cultural metta meditation."""

    def generate_single_culture(
        self,
        input_audio_path: str,
        culture: str,
        ...
    ) -> MettaResult:
        """Generate for a single culture (faster for testing)."""

    @staticmethod
    def create_manual_segments(
        timings: list[tuple[float, float, str]]
    ) -> list[SegmentTiming]:
        """Create segment timings manually if auto-detection fails."""
```

### MettaResult

```python
@dataclass
class MettaResult:
    audio: np.ndarray
    sample_rate: int
    cultures: list[str]
    duration_seconds: float

    def save(self, path: str) -> str:
        """Save to file."""
```

### SegmentTiming

```python
@dataclass
class SegmentTiming:
    start_sec: float
    end_sec: float
    phrase: str
```

## Manual Segment Timing

If automatic phrase detection doesn't work well for your recording:

```python
segments = MettaGenerator.create_manual_segments([
    (0.0, 3.5, "May you be happy"),
    (4.0, 7.5, "May you be peaceful"),
    (8.0, 12.0, "May you feel that you belong"),
])

result = generator.generate(
    input_audio_path="input/metta.wav",
    segments=segments,
    ...
)
```

## Environment Setup

Set your ElevenLabs API key:

```bash
export ELEVENLABS_API_KEY=your_key_here
```

Or create a `.env` file:

```
ELEVENLABS_API_KEY=your_key_here
```

## Running the Example

```bash
# Place your recording in input/
cp ~/my_metta_recording.wav metta_sdk/input/metta.wav

# Run the example
uv run python metta_sdk/example.py
```

## Output

The generated meditation will be approximately 10 minutes:
- 5 cultures x 3 phrases x ~40 seconds each
- Smooth 3-second crossfades between cultures
- Each culture section includes matching ambient sounds

## Dependencies

Uses existing SDK dependencies:
- ElevenLabs (speech-to-speech, sound generation)
- NumPy, SciPy (audio processing)
- librosa (silence detection)
- soundfile (audio I/O)
