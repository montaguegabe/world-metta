"""Main orchestration for cross-cultural metta meditation generation."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from librosa_sdk import MindfulAnalyzer

from .mixer import AudioMixer, SegmentTiming
from .plan import MettaPlan, PlanSection, PlanSegment
from .voices import CulturalVoiceMapper


@dataclass
class MettaResult:
    """Result of metta meditation generation."""

    audio: np.ndarray
    sample_rate: int
    duration_seconds: float
    plan_name: str = ""
    output_path: Optional[str] = None

    def save(self, path: str) -> str:
        """Save the meditation audio to file.

        Args:
            path: Output file path

        Returns:
            Path to saved file
        """
        import soundfile as sf

        sf.write(path, self.audio, self.sample_rate)
        self.output_path = path
        print(f"Saved meditation: {path}")
        return path


class MettaGenerator:
    """Generate cross-cultural metta meditations.

    Supports two modes:
    1. Plan-based: Load pre-segmented audio and execute a JSON plan
    2. Legacy: Auto-detect segments and transform through cultures
    """

    # Default metta phrases
    DEFAULT_PHRASES = [
        "May you be happy",
        "May you be peaceful",
        "May you feel that you belong",
    ]

    def __init__(self, api_key: Optional[str] = None, sample_rate: int = 44100):
        """Initialize the generator.

        Args:
            api_key: ElevenLabs API key
            sample_rate: Audio sample rate
        """
        self.voice_mapper = CulturalVoiceMapper(api_key)
        self.mixer = AudioMixer(sample_rate)
        self.sample_rate = sample_rate
        self._ambiance_cache: dict[str, np.ndarray] = {}

    def generate_from_plan(
        self,
        segments_dir: str,
        plan: MettaPlan,
        output_path: Optional[str] = None,
    ) -> MettaResult:
        """Generate meditation from a plan using pre-segmented audio.

        New approach: processes voices and ambiance separately, then mixes them
        with proper overlapping crossfades between ambient sounds.

        Args:
            segments_dir: Directory containing segmented audio files
            plan: MettaPlan defining the meditation structure
            output_path: Optional path to save output

        Returns:
            MettaResult with generated meditation
        """
        segments_path = Path(segments_dir)
        total_sections = len(plan.sections)
        print(f"Generating meditation: {plan.name}")
        print(f"Segments directory: {segments_path}")
        print(f"Total sections: {total_sections}")
        print("=" * 50)

        start_time = time.time()

        # === PHASE 1: Process voice segments (without ambiance) ===
        print("\n--- Phase 1: Processing voice segments ---")
        voice_segments = []  # List of (audio, ambiance_culture, section_index)

        for i, section in enumerate(plan.sections):
            section_start = time.time()
            print(f"\n[{i + 1}/{total_sections}] Section: {section.name}")

            for seg in section.segments:
                voice_audio = self._process_voice_only(segments_path, seg)
                voice_segments.append(
                    (voice_audio, seg.ambiance, seg.ambiance_volume, i)
                )

            elapsed = time.time() - section_start
            print(f"    Voice processed in {elapsed:.1f}s")

        # === PHASE 2: Calculate progressive gaps and total duration ===
        print("\n--- Phase 2: Calculating layout ---")

        # Calculate gap for each section (increases progressively)
        section_gaps = []
        for i in range(total_sections):
            gap = plan.gap_between_sec + (i * plan.gap_increase_per_section)
            section_gaps.append(gap)

        # Calculate voice positions (start times for each voice segment)
        voice_positions = []  # (start_sample, end_sample, ambiance_culture, ambiance_volume)
        current_pos = 0

        for i, (voice_audio, ambiance_culture, ambiance_vol, section_idx) in enumerate(
            voice_segments
        ):
            # Add gap before this segment (except first)
            if i > 0:
                gap_sec = section_gaps[section_idx]
                current_pos += int(gap_sec * self.sample_rate)

            start_pos = current_pos
            end_pos = current_pos + len(voice_audio)
            voice_positions.append((start_pos, end_pos, ambiance_culture, ambiance_vol))
            current_pos = end_pos

        # Add final pause
        final_pause_samples = int(plan.final_pause_sec * self.sample_rate)
        total_duration_samples = current_pos + final_pause_samples

        print(f"Total duration: {total_duration_samples / self.sample_rate:.1f}s")
        print(f"Progressive gaps: {[f'{g:.1f}s' for g in section_gaps]}")

        # === PHASE 3: Generate and overlay ambiance with crossfades ===
        print("\n--- Phase 3: Generating overlapping ambiance ---")

        ambiance_track = np.zeros(total_duration_samples, dtype=np.float32)
        overlap_sec = plan.ambiance_overlap_sec

        # Track which ambiance is currently playing for crossfade
        prev_ambiance = None
        prev_ambiance_end = 0

        for i, (start_pos, end_pos, ambiance_culture, ambiance_vol) in enumerate(
            voice_positions
        ):
            if ambiance_culture is None:
                prev_ambiance = None
                continue

            # Calculate ambiance start (before voice) and end (after voice)
            ambiance_start = max(0, start_pos - int(overlap_sec * self.sample_rate))
            ambiance_end = min(
                total_duration_samples, end_pos + int(overlap_sec * self.sample_rate)
            )
            ambiance_len = ambiance_end - ambiance_start

            # Get ambiance for this segment (request enough duration)
            ambiance_duration_needed = ambiance_len / self.sample_rate + 5
            ambiance = self._get_ambiance(ambiance_culture, ambiance_duration_needed)

            # Ensure we have enough samples, loop if necessary
            if len(ambiance) < ambiance_len:
                repeats = int(np.ceil(ambiance_len / len(ambiance)))
                ambiance = np.tile(ambiance, repeats)

            # Trim ambiance to fit
            ambiance_segment = ambiance[:ambiance_len].copy()

            # Apply fade in at start
            fade_in_samples = int(overlap_sec * self.sample_rate)
            if fade_in_samples > 0 and fade_in_samples < len(ambiance_segment):
                fade_in = np.linspace(0, 1, fade_in_samples)
                ambiance_segment[:fade_in_samples] *= fade_in

            # Apply fade out at end
            fade_out_samples = int(overlap_sec * self.sample_rate)
            if fade_out_samples > 0 and fade_out_samples < len(ambiance_segment):
                fade_out = np.linspace(1, 0, fade_out_samples)
                ambiance_segment[-fade_out_samples:] *= fade_out

            # Add to ambiance track (overlapping with previous)
            ambiance_track[ambiance_start:ambiance_end] += (
                ambiance_segment * ambiance_vol
            )

            prev_ambiance = ambiance_culture
            prev_ambiance_end = ambiance_end

        # Normalize ambiance to prevent clipping in overlapping regions
        max_amb = np.max(np.abs(ambiance_track))
        if max_amb > 0.5:
            ambiance_track = ambiance_track / max_amb * 0.5

        # === PHASE 4: Create voice track ===
        print("\n--- Phase 4: Assembling voice track ---")

        voice_track = np.zeros(total_duration_samples, dtype=np.float32)

        for i, (voice_audio, _, _, _) in enumerate(voice_segments):
            start_pos, end_pos, _, _ = voice_positions[i]
            voice_track[start_pos:end_pos] = voice_audio

        # === PHASE 5: Mix voice and ambiance ===
        print("\n--- Phase 5: Final mix ---")

        final_audio = voice_track + ambiance_track

        # Normalize
        max_val = np.max(np.abs(final_audio))
        if max_val > 0.95:
            final_audio = final_audio / max_val * 0.95

        # Apply final fade out
        final_audio = self.mixer.apply_fade(
            final_audio,
            fade_in_sec=1.0,
            fade_out_sec=plan.final_fade_out_sec,
        )

        total_elapsed = time.time() - start_time
        print(f"\nGeneration complete in {total_elapsed:.1f}s")

        result = MettaResult(
            audio=final_audio,
            sample_rate=self.sample_rate,
            duration_seconds=len(final_audio) / self.sample_rate,
            plan_name=plan.name,
        )

        if output_path:
            result.save(output_path)

        print(f"Duration: {result.duration_seconds:.1f}s")
        return result

    def _process_voice_only(
        self,
        segments_path: Path,
        seg: PlanSegment,
    ) -> np.ndarray:
        """Process a segment's voice without ambiance.

        Args:
            segments_path: Path to segments directory
            seg: Segment specification from plan

        Returns:
            Voice audio array (no ambiance)
        """
        # Load segment audio file
        segment_file = segments_path / f"{seg.subject}_{seg.occurrence}.wav"
        if not segment_file.exists():
            raise FileNotFoundError(f"Segment not found: {segment_file}")

        audio, sr = self.mixer.load_audio_file(str(segment_file))

        # Apply voice transformation if not original
        if seg.voice != "original":
            voice_desc = seg.voice if not seg.voice_id else f"{seg.voice} (explicit ID)"
            print(f"    Converting to {voice_desc} voice...", end=" ", flush=True)
            convert_start = time.time()
            audio_bytes = self.mixer.audio_to_bytes(audio)
            converted_bytes = self.voice_mapper.convert_speech(
                audio_data=audio_bytes,
                culture=seg.voice,
                voice_id=seg.voice_id,
            )
            audio, _ = self.mixer.load_audio(converted_bytes)
            print(f"done ({time.time() - convert_start:.1f}s)")

        return audio

    def _process_section(
        self,
        segments_path: Path,
        section: PlanSection,
    ) -> np.ndarray:
        """Process a single section of the plan.

        Args:
            segments_path: Path to segments directory
            section: Section to process

        Returns:
            Combined audio for this section
        """
        segment_audios = []

        for seg in section.segments:
            print(f"  Processing: {seg.subject} #{seg.occurrence} -> {seg.voice}")
            audio = self._process_segment(segments_path, seg)
            segment_audios.append(audio)

        # Assemble segments within section
        if len(segment_audios) == 1:
            return segment_audios[0]

        return self.mixer.assemble_meditation(
            segment_audios,
            crossfade_sec=section.crossfade_within_sec,
        )

    def _process_segment(
        self,
        segments_path: Path,
        seg: PlanSegment,
    ) -> np.ndarray:
        """Process a single segment according to plan.

        Args:
            segments_path: Path to segments directory
            seg: Segment specification from plan

        Returns:
            Processed audio array
        """
        # Load segment audio file (subject_occurrence.wav format)
        segment_file = segments_path / f"{seg.subject}_{seg.occurrence}.wav"
        if not segment_file.exists():
            raise FileNotFoundError(f"Segment not found: {segment_file}")

        audio, sr = self.mixer.load_audio_file(str(segment_file))

        # Apply voice transformation if not original
        if seg.voice != "original":
            voice_desc = seg.voice if not seg.voice_id else f"{seg.voice} (explicit ID)"
            print(f"    Converting to {voice_desc} voice...", end=" ", flush=True)
            convert_start = time.time()
            audio_bytes = self.mixer.audio_to_bytes(audio)
            converted_bytes = self.voice_mapper.convert_speech(
                audio_data=audio_bytes,
                culture=seg.voice,
                voice_id=seg.voice_id,  # Use explicit voice_id if provided
            )
            audio, _ = self.mixer.load_audio(converted_bytes)
            print(f"done ({time.time() - convert_start:.1f}s)")

        # Mix with ambiance if specified
        if seg.ambiance:
            # Get enough ambiance for voice + padding
            pad_before = 3.0  # seconds of ambiance before voice
            pad_after = 3.0  # seconds of ambiance after voice
            total_duration = (
                len(audio) / self.sample_rate + pad_before + pad_after + 2.0
            )

            ambiance = self._get_ambiance(seg.ambiance, total_duration)
            audio = self.mixer.mix_with_ambiance(
                voice_audio=audio,
                ambiance_audio=ambiance,
                voice_volume=1.0,
                ambiance_volume=seg.ambiance_volume,
                pad_before_sec=pad_before,
                pad_after_sec=pad_after,
            )

        # Apply segment-level fades if specified
        if seg.fade_in_sec > 0 or seg.fade_out_sec > 0:
            audio = self.mixer.apply_fade(
                audio,
                fade_in_sec=seg.fade_in_sec,
                fade_out_sec=seg.fade_out_sec,
            )

        return audio

    def _get_ambiance(self, culture: str, duration_sec: float) -> np.ndarray:
        """Get or generate ambiance for a culture.

        Args:
            culture: Culture name
            duration_sec: Required duration

        Returns:
            Ambiance audio array
        """
        # Check cache - loop if needed
        if culture in self._ambiance_cache:
            cached = self._ambiance_cache[culture]
            needed_samples = int(duration_sec * self.sample_rate)
            if len(cached) >= needed_samples:
                return cached[:needed_samples]
            else:
                # Loop the cached ambiance
                repeats = int(np.ceil(needed_samples / len(cached)))
                looped = np.tile(cached, repeats)[:needed_samples]
                return looped

        # Generate new ambiance (max 30s per API limit, will loop if needed)

        gen_duration = min(duration_sec, 30.0)
        print(
            f"    Generating {culture} ambiance ({gen_duration:.1f}s)...",
            end=" ",
            flush=True,
        )
        ambiance_start = time.time()
        ambiance_bytes = self.voice_mapper.generate_ambiance(
            culture=culture,
            duration_seconds=gen_duration,
        )
        ambiance, _ = self.mixer.load_audio(ambiance_bytes)
        print(f"done ({time.time() - ambiance_start:.1f}s)")

        # Cache it
        self._ambiance_cache[culture] = ambiance

        return ambiance[: int(duration_sec * self.sample_rate)]

    # === Legacy methods for backwards compatibility ===

    def detect_segments(
        self,
        audio_path: str,
        min_silence_ms: int = 500,
        silence_thresh_db: float = -40,
    ) -> list[SegmentTiming]:
        """Auto-detect phrase segments using silence detection.

        Args:
            audio_path: Path to audio file
            min_silence_ms: Minimum silence duration to detect
            silence_thresh_db: Silence threshold in dB

        Returns:
            List of detected segment timings
        """
        analyzer = MindfulAnalyzer(audio_path)
        gaps = analyzer.detect_silence_gaps(
            min_silence_ms=min_silence_ms,
            silence_thresh_db=silence_thresh_db,
        )

        duration = analyzer.get_duration()
        segments = []

        prev_end = 0.0
        for gap in gaps:
            if gap["start_sec"] > prev_end:
                phrase = (
                    self.DEFAULT_PHRASES[len(segments)]
                    if len(segments) < len(self.DEFAULT_PHRASES)
                    else ""
                )
                segments.append(
                    SegmentTiming(
                        start_sec=prev_end,
                        end_sec=gap["start_sec"],
                        phrase=phrase,
                    )
                )
            prev_end = gap["end_sec"]

        if prev_end < duration:
            phrase = (
                self.DEFAULT_PHRASES[len(segments)]
                if len(segments) < len(self.DEFAULT_PHRASES)
                else ""
            )
            segments.append(
                SegmentTiming(
                    start_sec=prev_end,
                    end_sec=duration,
                    phrase=phrase,
                )
            )

        return segments

    def generate(
        self,
        input_audio_path: str,
        cultures: Optional[list[str]] = None,
        segments: Optional[list[SegmentTiming]] = None,
        crossfade_ms: int = 3000,
        ambiance_volume: float = 0.3,
        output_path: Optional[str] = None,
    ) -> MettaResult:
        """Generate a cross-cultural metta meditation (legacy method).

        Args:
            input_audio_path: Path to user's metta recording
            cultures: List of cultures to include (default: all available)
            segments: Manual segment timings (auto-detected if not provided)
            crossfade_ms: Crossfade duration in milliseconds
            ambiance_volume: Volume level for ambient sounds (0-1)
            output_path: Optional path to save output

        Returns:
            MettaResult with generated meditation
        """
        if cultures is None:
            cultures = CulturalVoiceMapper.list_cultures()

        print(f"Generating metta meditation with cultures: {', '.join(cultures)}")

        input_audio, input_sr = self.mixer.load_audio_file(input_audio_path)
        print(f"Loaded input: {len(input_audio) / input_sr:.1f}s at {input_sr}Hz")

        if segments is None:
            print("Auto-detecting phrase segments...")
            segments = self.detect_segments(input_audio_path)
            print(f"Detected {len(segments)} segments")

        segment_audios = []
        for seg in segments:
            segment_audio = self.mixer.extract_segment(
                input_audio, seg.start_sec, seg.end_sec
            )
            segment_audios.append(segment_audio)

        cultural_sections = []
        crossfade_sec = crossfade_ms / 1000.0

        for culture in cultures:
            print(f"\nProcessing culture: {culture}")
            section = self._process_culture_legacy(
                culture=culture,
                segment_audios=segment_audios,
                segments=segments,
                ambiance_volume=ambiance_volume,
            )
            cultural_sections.append(section)

        print("\nAssembling final meditation...")
        final_audio = self.mixer.assemble_meditation(
            cultural_sections,
            crossfade_sec=crossfade_sec,
        )

        final_audio = self.mixer.apply_fade(
            final_audio,
            fade_in_sec=2.0,
            fade_out_sec=3.0,
        )

        result = MettaResult(
            audio=final_audio,
            sample_rate=self.sample_rate,
            duration_seconds=len(final_audio) / self.sample_rate,
        )

        if output_path:
            result.save(output_path)

        print(f"\nGeneration complete! Duration: {result.duration_seconds:.1f}s")
        return result

    def _process_culture_legacy(
        self,
        culture: str,
        segment_audios: list[np.ndarray],
        segments: list[SegmentTiming],
        ambiance_volume: float,
    ) -> np.ndarray:
        """Process all segments for a single culture (legacy method)."""
        converted_segments = []

        total_duration = (
            sum(len(audio) for audio in segment_audios) / self.sample_rate + 5.0
        )

        print(f"  Generating {culture} ambiance ({total_duration:.1f}s)...")
        ambiance_bytes = self.voice_mapper.generate_ambiance(
            culture=culture,
            duration_seconds=total_duration,
        )
        ambiance_audio, _ = self.mixer.load_audio(ambiance_bytes)

        for i, (segment_audio, segment_timing) in enumerate(
            zip(segment_audios, segments)
        ):
            print(
                f"  Converting segment {i + 1}/{len(segment_audios)}: {segment_timing.phrase[:30]}..."
            )

            segment_bytes = self.mixer.audio_to_bytes(segment_audio)
            converted_bytes = self.voice_mapper.convert_speech(
                audio_data=segment_bytes,
                culture=culture,
            )
            converted_audio, _ = self.mixer.load_audio(converted_bytes)
            converted_segments.append(converted_audio)

        gap_samples = int(0.5 * self.sample_rate)
        gap = np.zeros(gap_samples, dtype=np.float32)

        combined_voice = converted_segments[0]
        for segment in converted_segments[1:]:
            combined_voice = np.concatenate([combined_voice, gap, segment])

        cultural_audio = self.mixer.mix_with_ambiance(
            voice_audio=combined_voice,
            ambiance_audio=ambiance_audio,
            voice_volume=1.0,
            ambiance_volume=ambiance_volume,
        )

        return cultural_audio

    @staticmethod
    def list_cultures() -> list[str]:
        """List available cultures."""
        return CulturalVoiceMapper.list_cultures()

    @staticmethod
    def create_manual_segments(
        timings: list[tuple[float, float, str]],
    ) -> list[SegmentTiming]:
        """Create segment timings manually."""
        return [
            SegmentTiming(start_sec=start, end_sec=end, phrase=phrase)
            for start, end, phrase in timings
        ]
