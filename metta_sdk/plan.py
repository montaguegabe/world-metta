"""JSON-based meditation plan for metta generation."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PlanSegment:
    """A single segment in the meditation plan.

    Each segment references a grouped audio file containing all 3 phrases
    (happy, peaceful, belong) for a given subject+occurrence.
    """

    # Which audio segment to use (references subject_occurrence.wav)
    subject: str  # "I", "you", "we_all"
    occurrence: int = 1  # Which occurrence (1 or 2)

    # Voice transformation
    voice: str = "original"  # "original" or culture name like "japanese"
    voice_id: Optional[str] = None  # Explicit voice ID (overrides culture lookup)

    # Ambiance
    ambiance: Optional[str] = None  # Culture name for ambiance, or None for silence

    # Timing
    ambiance_volume: float = 0.3
    fade_in_sec: float = 0.0
    fade_out_sec: float = 0.0

    def to_dict(self) -> dict:
        d = {
            "subject": self.subject,
            "occurrence": self.occurrence,
            "voice": self.voice,
            "ambiance": self.ambiance,
            "ambiance_volume": self.ambiance_volume,
            "fade_in_sec": self.fade_in_sec,
            "fade_out_sec": self.fade_out_sec,
        }
        if self.voice_id:
            d["voice_id"] = self.voice_id
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PlanSegment":
        return cls(
            subject=data["subject"],
            occurrence=data.get("occurrence", 1),
            voice=data.get("voice", "original"),
            voice_id=data.get("voice_id"),
            ambiance=data.get("ambiance"),
            ambiance_volume=data.get("ambiance_volume", 0.3),
            fade_in_sec=data.get("fade_in_sec", 0.0),
            fade_out_sec=data.get("fade_out_sec", 0.0),
        )


@dataclass
class PlanSection:
    """A section of the meditation (multiple segments with shared crossfade)."""

    name: str
    segments: list[PlanSegment]
    crossfade_within_sec: float = 0.5  # Crossfade between segments within section
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "crossfade_within_sec": self.crossfade_within_sec,
            "segments": [s.to_dict() for s in self.segments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanSection":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            crossfade_within_sec=data.get("crossfade_within_sec", 0.5),
            segments=[PlanSegment.from_dict(s) for s in data["segments"]],
        )


@dataclass
class MettaPlan:
    """Complete meditation plan."""

    name: str
    description: str
    sections: list[PlanSection]
    crossfade_between_sec: float = 3.0  # Crossfade between sections
    gap_between_sec: float = 0.0  # Base silence gap between sections
    gap_increase_per_section: float = 0.0  # Gap increases by this much each section
    ambiance_overlap_sec: float = (
        8.0  # How long ambient sounds overlap during transitions
    )
    final_pause_sec: float = 5.0  # Silence at the very end before fade
    final_fade_out_sec: float = 3.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "crossfade_between_sec": self.crossfade_between_sec,
            "gap_between_sec": self.gap_between_sec,
            "gap_increase_per_section": self.gap_increase_per_section,
            "ambiance_overlap_sec": self.ambiance_overlap_sec,
            "final_pause_sec": self.final_pause_sec,
            "final_fade_out_sec": self.final_fade_out_sec,
            "sections": [s.to_dict() for s in self.sections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MettaPlan":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            crossfade_between_sec=data.get("crossfade_between_sec", 3.0),
            gap_between_sec=data.get("gap_between_sec", 0.0),
            gap_increase_per_section=data.get("gap_increase_per_section", 0.0),
            ambiance_overlap_sec=data.get("ambiance_overlap_sec", 8.0),
            final_pause_sec=data.get("final_pause_sec", 5.0),
            final_fade_out_sec=data.get("final_fade_out_sec", 3.0),
            sections=[PlanSection.from_dict(s) for s in data["sections"]],
        )

    def save(self, path: str) -> str:
        """Save plan to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Saved plan: {path}")
        return path

    @classmethod
    def load(cls, path: str) -> "MettaPlan":
        """Load plan from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_expanding_metta_plan() -> MettaPlan:
    """Create the expanding circles metta plan.

    Structure based on actual recording order (you -> I -> we all):
    1. Original voice, "may I" phrases, no ambiance (intimate/personal)
    2. "May you" with different cultural voices
    3. "May we all" with cultural voice (only 1 occurrence available)

    Each segment contains all 3 phrases (happy, peaceful, belong).
    """
    plan = MettaPlan(
        name="Expanding Circles Metta",
        description="Metta meditation expanding from self to others to all beings, with cultural voices",
        crossfade_between_sec=3.0,
        final_fade_out_sec=5.0,
        sections=[
            # Section 1: Original voice, self-directed, no ambiance
            PlanSection(
                name="Self (May I) - Original",
                description="Personal, intimate self-compassion in original voice",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="I", occurrence=1, voice="original", ambiance=None
                    ),
                    PlanSegment(
                        subject="I", occurrence=2, voice="original", ambiance=None
                    ),
                ],
            ),
            # Section 2: Original voice for "may you" - no transformation yet
            PlanSection(
                name="Other (May You) - Original",
                description="Extending compassion to others, still in original voice",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="you", occurrence=1, voice="original", ambiance=None
                    ),
                ],
            ),
            # Section 3: Japanese voice for "may you"
            PlanSection(
                name="Other (May You) - Japanese",
                description="Compassion with Japanese zen ambiance",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="you",
                        occurrence=2,
                        voice="japanese",
                        ambiance="japanese",
                        ambiance_volume=0.25,
                    ),
                ],
            ),
            # Section 4: Indian voice for "may I"
            PlanSection(
                name="Self (May I) - Indian",
                description="Self-compassion with Indian temple ambiance",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="I",
                        occurrence=1,
                        voice="indian",
                        ambiance="indian",
                        ambiance_volume=0.25,
                    ),
                ],
            ),
            # Section 5: African voice for "may we all"
            PlanSection(
                name="All Beings (May We All) - African",
                description="Universal compassion with African ambiance",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="we_all",
                        occurrence=1,
                        voice="african",
                        ambiance="african",
                        ambiance_volume=0.3,
                    ),
                ],
            ),
            # Section 6: Celtic voice for "may we all" (reusing occurrence=1 since only 1 available)
            PlanSection(
                name="All Beings (May We All) - Celtic",
                description="Universal compassion with Celtic ambiance",
                crossfade_within_sec=1.0,
                segments=[
                    PlanSegment(
                        subject="we_all",
                        occurrence=1,
                        voice="celtic",
                        ambiance="celtic",
                        ambiance_volume=0.3,
                        fade_out_sec=2.0,
                    ),
                ],
            ),
        ],
    )

    return plan


def create_simple_test_plan() -> MettaPlan:
    """Create a simple test plan with just a few segments."""
    return MettaPlan(
        name="Simple Test",
        description="Quick test with minimal segments",
        crossfade_between_sec=2.0,
        final_fade_out_sec=3.0,
        sections=[
            PlanSection(
                name="Original",
                description="Original voice test",
                segments=[
                    PlanSegment(
                        subject="I", occurrence=1, voice="original", ambiance=None
                    ),
                ],
            ),
            PlanSection(
                name="Japanese",
                description="Japanese voice test",
                segments=[
                    PlanSegment(
                        subject="you",
                        occurrence=1,
                        voice="japanese",
                        ambiance="japanese",
                    ),
                ],
            ),
        ],
    )
