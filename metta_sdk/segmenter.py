"""Transcribe and segment metta meditation recordings using ElevenLabs STT."""

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import librosa
import soundfile as sf
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


@dataclass
class MettaPhrase:
    """A single metta phrase with timing info."""

    subject: str  # "I", "you", "we_all"
    quality: str  # "happy", "peaceful", "belong"
    text: str
    start_sec: float
    end_sec: float
    occurrence: int  # 1 or 2 (first or second time)

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SegmentFile:
    """Reference to an extracted audio segment file."""

    path: str
    phrase: MettaPhrase

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "phrase": self.phrase.to_dict(),
        }


class MettaSegmenter:
    """Transcribe and segment metta meditation recordings."""

    # Patterns for detecting metta phrases
    SUBJECT_PATTERNS = {
        "I": r"\bmay\s+i\b",
        "you": r"\bmay\s+you\b",
        "we_all": r"\bmay\s+we\s+all\b",
    }

    QUALITY_PATTERNS = {
        "happy": r"\b(happy|happiness)\b",
        "peaceful": r"\b(peaceful|peace)\b",
        "belong": r"\b(belong|belonging)\b",
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize segmenter.

        Args:
            api_key: ElevenLabs API key
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key required. Set ELEVENLABS_API_KEY environment variable."
            )

        self.client = ElevenLabs(api_key=self.api_key)

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio file with word-level timestamps.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription result with words and timestamps
        """
        print(f"Transcribing: {audio_path}")

        with open(audio_path, "rb") as f:
            result = self.client.speech_to_text.convert(
                file=f,
                model_id="scribe_v2",
                tag_audio_events=False,
                diarize=False,
            )

        print(f"Transcription: {result.text}")
        return result

    def detect_phrases(self, transcription) -> list[MettaPhrase]:
        """Detect metta phrases from transcription with timestamps.

        Args:
            transcription: ElevenLabs transcription result

        Returns:
            List of detected MettaPhrase objects
        """
        words = transcription.words
        phrases = []

        # Track occurrences per subject+quality combo
        occurrence_counts: dict[tuple[str, str], int] = {}

        i = 0
        while i < len(words):
            word = words[i]
            if word.type != "word":
                i += 1
                continue

            # Check for "may" to start a phrase
            if word.text.lower() != "may":
                i += 1
                continue

            # Look ahead to find subject and quality
            phrase_words = [word]
            subject = None
            quality = None
            j = i + 1

            # Collect words until we find quality or hit a limit
            while j < len(words) and j < i + 15:  # Max 15 words per phrase
                w = words[j]
                if w.type == "word":
                    phrase_words.append(w)

                    # Check for subject
                    phrase_text = " ".join(pw.text.lower() for pw in phrase_words)
                    for subj, pattern in self.SUBJECT_PATTERNS.items():
                        if re.search(pattern, phrase_text) and subject is None:
                            subject = subj

                    # Check for quality
                    for qual, pattern in self.QUALITY_PATTERNS.items():
                        if re.search(pattern, w.text.lower()):
                            quality = qual
                            break

                    if quality:
                        break
                j += 1

            if subject and quality:
                # Found a complete phrase
                key = (subject, quality)
                occurrence_counts[key] = occurrence_counts.get(key, 0) + 1

                phrase = MettaPhrase(
                    subject=subject,
                    quality=quality,
                    text=" ".join(pw.text for pw in phrase_words),
                    start_sec=phrase_words[0].start,
                    end_sec=phrase_words[-1].end,
                    occurrence=occurrence_counts[key],
                )
                phrases.append(phrase)
                print(
                    f"  Found: [{subject}] [{quality}] #{occurrence_counts[key]}: {phrase.text}"
                )
                i = j + 1
            else:
                i += 1

        return phrases

    def extract_segments(
        self,
        audio_path: str,
        phrases: list[MettaPhrase],
        output_dir: str,
        padding_sec: float = 0.1,
    ) -> list[SegmentFile]:
        """Extract audio segments grouped by subject+occurrence.

        Groups all qualities (happy, peaceful, belong) for each subject+occurrence
        into a single audio file.

        Args:
            audio_path: Path to source audio
            phrases: List of detected phrases
            output_dir: Directory to save segments
            padding_sec: Padding to add before/after each segment

        Returns:
            List of SegmentFile objects (one per subject+occurrence group)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Load audio (librosa handles m4a and other formats)
        audio, sr = librosa.load(audio_path, sr=None)

        # Group phrases by subject+occurrence
        groups: dict[tuple[str, int], list[MettaPhrase]] = {}
        for phrase in phrases:
            key = (phrase.subject, phrase.occurrence)
            if key not in groups:
                groups[key] = []
            groups[key].append(phrase)

        segments = []
        for (subject, occurrence), group_phrases in groups.items():
            # Sort by start time to ensure correct order
            group_phrases.sort(key=lambda p: p.start_sec)

            # Get time range for entire group (first phrase start to last phrase end)
            start_sec = group_phrases[0].start_sec - padding_sec
            end_sec = group_phrases[-1].end_sec + padding_sec

            start_sample = max(0, int(start_sec * sr))
            end_sample = min(len(audio), int(end_sec * sr))

            # Extract segment
            segment_audio = audio[start_sample:end_sample]

            # Generate filename: subject_occurrence.wav
            filename = f"{subject}_{occurrence}.wav"
            filepath = output_path / filename

            # Save segment
            sf.write(str(filepath), segment_audio, sr)

            # Create a representative phrase for the group
            combined_text = " | ".join(p.text for p in group_phrases)
            representative_phrase = MettaPhrase(
                subject=subject,
                quality="all",  # Combined
                text=combined_text,
                start_sec=group_phrases[0].start_sec,
                end_sec=group_phrases[-1].end_sec,
                occurrence=occurrence,
            )

            print(
                f"  Saved: {filepath} ({len(group_phrases)} phrases, {end_sec - start_sec:.1f}s)"
            )
            segments.append(
                SegmentFile(path=str(filepath), phrase=representative_phrase)
            )

        # Sort by original order in recording
        segments.sort(key=lambda s: s.phrase.start_sec)

        return segments

    def segment_audio(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        save_transcription: bool = True,
    ) -> tuple[list[SegmentFile], dict]:
        """Full pipeline: transcribe, detect phrases, extract segments.

        Args:
            audio_path: Path to audio file
            output_dir: Output directory (default: next to audio file)
            save_transcription: Whether to save raw transcription

        Returns:
            Tuple of (segment files, transcription data)
        """
        audio_path = Path(audio_path)
        if output_dir is None:
            output_dir = audio_path.parent / "segments"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Transcribe
        transcription = self.transcribe(str(audio_path))

        # Save raw transcription
        if save_transcription:
            trans_path = output_path / "transcription.json"
            trans_data = {
                "text": transcription.text,
                "language_code": transcription.language_code,
                "words": [
                    {
                        "text": w.text,
                        "start": w.start,
                        "end": w.end,
                        "type": w.type,
                    }
                    for w in transcription.words
                ],
            }
            with open(trans_path, "w") as f:
                json.dump(trans_data, f, indent=2)
            print(f"Saved transcription: {trans_path}")

        # Detect phrases
        print("\nDetecting metta phrases...")
        phrases = self.detect_phrases(transcription)
        print(f"Found {len(phrases)} phrases")

        # Extract segments
        print("\nExtracting audio segments...")
        segments = self.extract_segments(str(audio_path), phrases, str(output_dir))

        # Save segments manifest
        manifest_path = output_path / "segments.json"
        with open(manifest_path, "w") as f:
            json.dump([s.to_dict() for s in segments], f, indent=2)
        print(f"\nSaved manifest: {manifest_path}")

        return segments, trans_data


def segment_metta_recording(audio_path: str, output_dir: Optional[str] = None):
    """Convenience function to segment a metta recording.

    Args:
        audio_path: Path to combined metta recording
        output_dir: Output directory for segments
    """
    segmenter = MettaSegmenter()
    segments, _ = segmenter.segment_audio(audio_path, output_dir)

    print("\n=== Segmentation Complete ===")
    print(f"Total segments: {len(segments)}")

    # Summary by subject
    by_subject = {}
    for seg in segments:
        subj = seg.phrase.subject
        by_subject[subj] = by_subject.get(subj, 0) + 1

    for subj, count in by_subject.items():
        print(f"  {subj}: {count} phrases")

    return segments
