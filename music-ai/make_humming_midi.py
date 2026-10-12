import argparse
from pathlib import Path

from src.audio_loader import load_audio
from src.tempo_detector import detect_tempo

from src.humming_pitch import (
    detect_pitch,
    group_pitch_to_notes,
)

from src.rhythm_analyzer import (
    analyze_rhythm,
    get_subdivision_result,
    quantize_notes_to_beats,
    detect_phrases,
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
        description=(
            "허밍을 Beat 기반으로 분석해 "
            "멜로디 MIDI와 화음 MIDI를 생성합니다."
        )
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
        help="Pad MIDI 출력 경로",
    )

    parser.add_argument(
        "--combined-output",
        default="output/humming_with_pad.mid",
        help="통합 MIDI 출력 경로",
    )

    parser.add_argument(
        "--bpm",
        type=float,
        default=None,
        help=(
            "BPM을 직접 지정합니다. "
            "생략하면 오디오에서 자동 분석합니다."
        ),
    )

    parser.add_argument(
        "--subdivision",
        type=int,
        choices=[1, 2, 4],
        default=4,
        help=(
            "Quantize 해상도. "
            "1=4분음표, 2=8분음표, "
            "4=16분음표"
        ),
    )

    parser.add_argument(
        "--quantize-strength",
        type=float,
        default=1.0,
        help=(
            "Quantize 강도. "
            "0.0=원본, 1.0=완전 보정"
        ),
    )

    parser.add_argument(
        "--beats-per-chord",
        type=float,
        default=4.0,
        help=(
            "코드 하나가 유지되는 기본 박 수. "
            "기본값 4.0"
        ),
    )

    return parser.parse_args()


def print_rhythm(
    notes,
):
    print(
        "\n=== Quantized Melody ==="
    )

    for note in notes:
        print(
            f"{note['note']:4s}  "
            f"beat "
            f"{note['beat_start']:5.2f} "
            f"- "
            f"{note['beat_end']:5.2f}  "
            f"duration "
            f"{note['beat_duration']:4.2f}  "
            f"time "
            f"{note['start']:6.3f}s "
            f"- "
            f"{note['end']:6.3f}s"
        )


def print_phrases(
    phrases,
):
    print(
        "\n=== Phrase Analysis ==="
    )

    for phrase in phrases:
        print(
            f"Phrase "
            f"{phrase['phrase']}: "
            f"beat "
            f"{phrase['start_beat']:.2f} "
            f"- "
            f"{phrase['end_beat']:.2f}"
        )


def print_harmony(
    progression,
):
    print(
        "\n=== Harmony ==="
    )

    for chord in progression:
        chord_names = [
            NOTE_NAMES[
                pitch_class
            ]
            for pitch_class
            in chord["notes"]
        ]

        print(
            f"beat "
            f"{chord['start_beat']:5.2f} "
            f"- "
            f"{chord['end_beat']:5.2f}  "
            f"{'-'.join(chord_names)}"
        )


def main():
    args = parse_args()

    input_path = Path(
        args.input
    )

    if not input_path.exists():
        print(
            f"파일을 찾을 수 없습니다: "
            f"{input_path}"
        )
        return

    if not (
        0.0
        <= args.quantize_strength
        <= 1.0
    ):
        print(
            "--quantize-strength는 "
            "0.0에서 1.0 사이여야 합니다."
        )
        return

    print(
        f"\n허밍 파일: "
        f"{input_path}"
    )

    # 1. 오디오 로드
    print(
        "\n오디오 분석 중..."
    )

    y, sr = load_audio(
        input_path
    )

    # 2. BPM
    detected_bpm, _ = detect_tempo(
        y,
        sr
    )

    if args.bpm is None:
        bpm = float(
            detected_bpm
        )
    else:
        bpm = float(
            args.bpm
        )

    print(
        f"분석 BPM: "
        f"{detected_bpm:.2f}"
    )

    print(
        f"사용 BPM: "
        f"{bpm:.2f}"
    )

    # 3. 피치 분석
    print(
        "\n피치 분석 중..."
    )

    pitch_frames = detect_pitch(
        y,
        sr
    )

    if not pitch_frames:
        print(
            "피치를 검출하지 못했습니다."
        )
        return

    # 4. 원본 노트 생성
    raw_notes = group_pitch_to_notes(
        pitch_frames
    )

    if not raw_notes:
        print(
            "유효한 멜로디 노트를 "
            "검출하지 못했습니다."
        )
        return

    print(
        f"검출된 노트: "
        f"{len(raw_notes)}개"
    )

    # 5. Grid 분석
    rhythm_result = analyze_rhythm(
        notes=raw_notes,
        bpm=bpm,
    )

    if rhythm_result is None:
        print(
            "리듬 분석에 실패했습니다."
        )
        return

    subdivision_result = (
        get_subdivision_result(
            rhythm_result,
            args.subdivision,
        )
    )

    if subdivision_result is None:
        print(
            "요청한 Grid를 "
            "찾지 못했습니다."
        )
        return

    offset = (
        subdivision_result[
            "offset"
        ]
    )

    print(
        f"\nQuantize Grid: "
        f"1/{4 * args.subdivision} note"
    )

    print(
        f"Grid offset: "
        f"{offset:.3f}s"
    )

    print(
        f"Grid 평균 오차: "
        f"{subdivision_result['average_error']:.3f}s"
    )

    # 6. Beat 기반 Quantize
    notes = quantize_notes_to_beats(
        notes=raw_notes,
        bpm=bpm,
        offset=offset,
        subdivision=args.subdivision,
        strength=args.quantize_strength,
    )

    print_rhythm(
        notes
    )

    # 7. Phrase 분석
    phrases = detect_phrases(
        notes=notes,
        bpm=bpm,
        min_silence_beats=0.5,
    )

    print_phrases(
        phrases
    )

    # 8. Key 분석
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

    # 9. Beat 기반 코드 생성
    progression = create_chord_progression(
        notes=notes,
        key=key,
        bpm=bpm,
        offset=offset,
        beats_per_chord=args.beats_per_chord,
    )

    print_harmony(
        progression
    )

    # 10. 출력 경로
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

    # 11. MIDI 생성
    create_melody_midi(
        notes=notes,
        output_path=melody_output,
        bpm=bpm,
    )

    create_pad_midi(
        progression=progression,
        output_path=pad_output,
        bpm=bpm,
    )

    create_combined_midi(
        notes=notes,
        progression=progression,
        output_path=combined_output,
        bpm=bpm,
    )

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