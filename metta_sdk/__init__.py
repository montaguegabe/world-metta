"""Cross-cultural metta meditation generation SDK.

This SDK generates culturally diverse metta meditations by:
1. Transcribing and segmenting the user's metta recording
2. Executing a JSON-based meditation plan
3. Applying ElevenLabs speech-to-speech conversion with cultural voices
4. Layering culturally-appropriate ambient sounds
5. Crossfading segments together for a seamless meditation experience

Workflow:
    # Step 1: Segment the recording
    from metta_sdk import MettaSegmenter
    segmenter = MettaSegmenter()
    segments, _ = segmenter.segment_audio("input/combined.m4a", "segments/")

    # Step 2: Create or load a plan
    from metta_sdk import MettaPlan, create_expanding_metta_plan
    plan = create_expanding_metta_plan()
    plan.save("plan.json")

    # Step 3: Generate meditation from plan
    from metta_sdk import MettaGenerator
    generator = MettaGenerator()
    result = generator.generate_from_plan("segments/", plan)
    result.save("output/meditation.wav")
"""

from .generator import MettaGenerator, MettaResult
from .mixer import AudioMixer, SegmentTiming
from .plan import (
    MettaPlan,
    PlanSection,
    PlanSegment,
    create_expanding_metta_plan,
    create_simple_test_plan,
)
from .segmenter import MettaPhrase, MettaSegmenter, SegmentFile, segment_metta_recording
from .voices import CULTURAL_VOICES, CulturalVoice, CulturalVoiceMapper

__all__ = [
    # Generator
    "MettaGenerator",
    "MettaResult",
    # Segmenter
    "MettaSegmenter",
    "MettaPhrase",
    "SegmentFile",
    "segment_metta_recording",
    # Plan
    "MettaPlan",
    "PlanSection",
    "PlanSegment",
    "create_expanding_metta_plan",
    "create_simple_test_plan",
    # Mixer
    "AudioMixer",
    "SegmentTiming",
    # Voices
    "CulturalVoice",
    "CulturalVoiceMapper",
    "CULTURAL_VOICES",
]
