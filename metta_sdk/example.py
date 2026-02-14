#!/usr/bin/env python3
"""Example script for generating cross-cultural metta meditations.

Workflow:
1. Place your combined metta recording in metta_sdk/input/combined.m4a
2. Run this script to:
   a. Transcribe and segment the recording
   b. Generate a default plan (or load custom plan.json)
   c. Generate the final meditation

Usage:
    uv run python metta_sdk/example.py
"""

from pathlib import Path

from metta_sdk import (
    MettaGenerator,
    MettaPlan,
    MettaSegmenter,
    create_expanding_metta_plan,
    create_simple_test_plan,
)


def main():
    """Main workflow: segment -> plan -> generate."""
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    segments_dir = base_dir / "segments"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # Find input file
    input_files = (
        list(input_dir.glob("*.m4a"))
        + list(input_dir.glob("*.wav"))
        + list(input_dir.glob("*.mp3"))
    )
    if not input_files:
        print("No audio file found in metta_sdk/input/")
        print("\nPlease record yourself saying the metta phrases:")
        print("  2x: May I be happy, may I be peaceful, may I feel that I belong")
        print(
            "  2x: May you be happy, may you be peaceful, may you feel that you belong"
        )
        print(
            "  2x: May we all be happy, may we all be peaceful, may we all feel that we belong"
        )
        print("\nSave as metta_sdk/input/combined.m4a (or .wav/.mp3)")
        return

    input_path = input_files[0]
    print(f"Using input file: {input_path}")

    # Step 1: Segment the recording (if not already done)
    segments_manifest = segments_dir / "segments.json"
    if not segments_manifest.exists():
        print("\n=== Step 1: Segmenting Recording ===")
        segmenter = MettaSegmenter()
        segments, _ = segmenter.segment_audio(str(input_path), str(segments_dir))
        print(f"Created {len(segments)} segments")
    else:
        print("\n=== Step 1: Using existing segments ===")
        print(f"Found: {segments_manifest}")

    # Step 2: Create or load plan
    plan_path = base_dir / "plan.json"
    if plan_path.exists():
        print("\n=== Step 2: Loading existing plan ===")
        plan = MettaPlan.load(str(plan_path))
        print(f"Loaded plan: {plan.name}")
    else:
        print("\n=== Step 2: Creating default plan ===")
        plan = create_expanding_metta_plan()
        plan.save(str(plan_path))
        print(f"Saved plan to: {plan_path}")
        print("Edit this file to customize the meditation structure!")

    # Step 3: Generate meditation
    print("\n=== Step 3: Generating Meditation ===")
    generator = MettaGenerator()
    result = generator.generate_from_plan(
        segments_dir=str(segments_dir),
        plan=plan,
        output_path=str(output_dir / "metta_meditation.wav"),
    )

    print("\n=== Complete! ===")
    print(f"Duration: {result.duration_seconds:.1f} seconds")
    print(f"Output: {result.output_path}")


def segment_only():
    """Just segment the recording without generating."""
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    segments_dir = base_dir / "segments"

    input_files = list(input_dir.glob("*.m4a")) + list(input_dir.glob("*.wav"))
    if not input_files:
        print("No input file found")
        return

    segmenter = MettaSegmenter()
    segments, _ = segmenter.segment_audio(str(input_files[0]), str(segments_dir))

    print(f"\nSegmented into {len(segments)} phrases:")
    for seg in segments:
        print(
            f"  {seg.phrase.subject}/{seg.phrase.quality} #{seg.phrase.occurrence}: {seg.path}"
        )


def generate_test():
    """Generate a quick test with minimal segments."""
    base_dir = Path(__file__).parent
    segments_dir = base_dir / "segments"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    if not (segments_dir / "segments.json").exists():
        print("Run segment_only() first to create segments")
        return

    plan = create_simple_test_plan()
    generator = MettaGenerator()
    result = generator.generate_from_plan(
        segments_dir=str(segments_dir),
        plan=plan,
        output_path=str(output_dir / "test_meditation.wav"),
    )
    print(f"Test meditation: {result.output_path}")


def show_plan_structure():
    """Display the default plan structure."""
    plan = create_expanding_metta_plan()

    print(f"Plan: {plan.name}")
    print(f"Description: {plan.description}")
    print(f"Crossfade between sections: {plan.crossfade_between_sec}s")
    print(f"Final fade out: {plan.final_fade_out_sec}s")
    print()

    for section in plan.sections:
        print(f"Section: {section.name}")
        print(f"  Description: {section.description}")
        print(f"  Crossfade within: {section.crossfade_within_sec}s")
        print("  Segments:")
        for seg in section.segments:
            voice_info = f"voice={seg.voice}"
            if seg.ambiance:
                voice_info += f", ambiance={seg.ambiance}"
            print(f"    - {seg.subject} #{seg.occurrence}: {voice_info}")
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "segment":
            segment_only()
        elif cmd == "test":
            generate_test()
        elif cmd == "plan":
            show_plan_structure()
        else:
            print(f"Unknown command: {cmd}")
            print("Commands: segment, test, plan")
    else:
        main()
