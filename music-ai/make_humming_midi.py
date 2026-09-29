import argparse
from pathlib import Path

from src.audio_loader import load_audio

from src.humming_pitch import (
    detect_pitch,
    group_pitch_to_notes,
    smooth_note_lengths,
)

from src.humming_midi import (
    create_melody_midi,
    create_pad_midi,
    create_combined_midi,
)

from src.harmony import (
    NOTE_NAMES,
    detect_melody_key,
    create_chord_progression,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="허밍 음원을 멜로디 MIDI와 화음 Pad MIDI로 변환합니다."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="허밍 음원 파일 경로",
    )

    parser.add_argument(
        "--output",
        default="output/humming.mid",
        help="멜로디 MIDI 출력 경로",
    )

    parser.add_argument(
        "--pad-output",
        default="output/pad.mid",
        help="화음 Pad MIDI 출력 경로",
    )

    parser.add_argument(
        "--combined-output",
        default="output/humming_with_pad.mid",
        help="멜로디와 화음을 합친 MIDI 출력 경로",
    )

    parser.add_argument(
        "--bpm",
        type=float,
        default=120.0,
        help="MIDI BPM",
    )

    parser.add_argument(
        "--chord-seconds",
        type=float,
        default=2.0,
        help="화음이 유지되는 기본 시간(초)",
    )

    return parser.parse_args()


def print_melody(notes):
    print("\n=== Melody ===")

    for note in notes:
        print(
            f"{note['start']:6.2f}s - "
            f"{note['end']:6.2f}s  "
            f"{note['note']:4s}  "
            f"MIDI {note['midi']:3d}"
        )


def print_harmony(progression):
    print("\n=== Harmony ===")

    for chord in progression:
        chord_names = [
            NOTE_NAMES[pitch_class]
            for pitch_class in chord["notes"]
        ]

        print(
            f"{chord['start']:6.2f}s - "
            f"{chord['end']:6.2f}s  "
            f"{'-'.join(chord_names)}"
        )


def main():
    args = parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(
            f"파일을 찾을 수 없습니다: "
            f"{input_path}"
        )
        return

    print(f"\n허밍 파일: {input_path}")

    # 1. 허밍 오디오 로드
    print("\n피치 분석 중...")

    y, sr = load_audio(
        input_path
    )

    # 2. 프레임 단위 피치 추출
    pitch_frames = detect_pitch(
        y,
        sr
    )

    if not pitch_frames:
        print(
            "피치를 검출하지 못했습니다."
        )
        return

    # 3. 실제 노트 단위로 묶기
    notes = group_pitch_to_notes(
        pitch_frames
    )

    # 4. 짧은 공백을 부드럽게 연결
    notes = smooth_note_lengths(
        notes
    )

    if not notes:
        print(
            "유효한 멜로디 노트를 "
            "검출하지 못했습니다."
        )
        return

    print(
        f"검출된 노트: "
        f"{len(notes)}개"
    )

    print_melody(
        notes
    )

    # 5. 멜로디 Key 추정
    key = detect_melody_key(
        notes
    )

    if key is None:
        print(
            "\nKey를 추정하지 못했습니다."
        )
        return

    print(
        f"\n추정 Key: "
        f"{key['name']}"
    )

    # 6. 화음 진행 생성
    progression = create_chord_progression(
        notes=notes,
        key=key,
        chord_seconds=args.chord_seconds,
    )

    print_harmony(
        progression
    )

    # 7. 출력 경로 준비
    melody_output = Path(
        args.output
    )

    pad_output = Path(
        args.pad_output
    )

    combined_output = Path(
        args.combined_output
    )

    melody_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pad_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 8. 멜로디 MIDI 생성
    create_melody_midi(
        notes=notes,
        output_path=melody_output,
        bpm=args.bpm,
    )

    # 9. Pad MIDI 생성
    create_pad_midi(
        progression=progression,
        output_path=pad_output,
        bpm=args.bpm,
    )

    # 10. 멜로디 + Pad 통합 MIDI 생성
    create_combined_midi(
        notes=notes,
        progression=progression,
        output_path=combined_output,
        bpm=args.bpm,
    )

    # 11. 결과 출력
    print(
        f"\n멜로디 MIDI 생성 완료: "
        f"{melody_output}"
    )

    print(
        f"Pad MIDI 생성 완료: "
        f"{pad_output}"
    )

    print(
        f"통합 MIDI 생성 완료: "
        f"{combined_output}"
    )


if __name__ == "__main__":
    main()