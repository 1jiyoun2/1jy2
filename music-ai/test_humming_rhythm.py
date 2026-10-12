import sys
from pathlib import Path

from src.audio_loader import load_audio

from src.tempo_detector import detect_tempo

from src.humming_pitch import (
    detect_pitch,
    group_pitch_to_notes,
    smooth_note_lengths,
)

from src.rhythm_analyzer import (
    analyze_rhythm,
    get_subdivision_result,
    map_notes_to_grid,
    detect_phrases,
    quantize_notes_to_grid,
)


def subdivision_name(subdivision):
    names = {
        1: "4분음표",
        2: "8분음표",
        4: "16분음표",
    }

    return names.get(
        subdivision,
        f"1/{subdivision}",
    )


def main():
    if len(sys.argv) < 2:
        print(
            "사용법: "
            "python test_humming_rhythm.py "
            "<허밍파일> [quantize_strength]"
        )
        sys.exit(1)

    audio_path = Path(
        sys.argv[1]
    )

    quantize_strength = 0.75

    if len(sys.argv) >= 3:
        quantize_strength = float(
            sys.argv[2]
        )

    if not audio_path.exists():
        print(
            f"파일을 찾을 수 없습니다: "
            f"{audio_path}"
        )
        sys.exit(1)

    print(
        f"\n허밍 파일: {audio_path}"
    )

    # ---------------------------------
    # 1. 오디오 로드
    # ---------------------------------

    print(
        "\n오디오 로드 중..."
    )

    y, sr = load_audio(
        audio_path
    )

    # ---------------------------------
    # 2. BPM 분석
    # ---------------------------------

    print(
        "BPM 분석 중..."
    )

    bpm, _ = detect_tempo(
        y,
        sr
    )

    print(
        f"BPM: {bpm:.2f}"
    )

    # ---------------------------------
    # 3. 피치 분석
    # ---------------------------------

    print(
        "피치 분석 중..."
    )

    pitch_frames = detect_pitch(
        y,
        sr
    )

    if not pitch_frames:
        print(
            "피치를 검출하지 못했습니다."
        )
        sys.exit(1)

    # ---------------------------------
    # 4. 피치 프레임을 멜로디 노트로 묶기
    # ---------------------------------

    notes = group_pitch_to_notes(
        pitch_frames
    )

    if not notes:
        print(
            "유효한 멜로디 노트를 "
            "검출하지 못했습니다."
        )
        sys.exit(1)

    # MIDI 재생용으로 길이를 부드럽게 만든 버전.
    # 현재 리듬 분석에는 사용하지 않는다.
    smoothed_notes = smooth_note_lengths(
        notes
    )

    print(
        f"검출된 멜로디 노트: "
        f"{len(notes)}개"
    )

    # ---------------------------------
    # 5. Grid 분석
    # ---------------------------------

    print(
        "\n리듬 Grid 분석 중..."
    )

    result = analyze_rhythm(
        notes=notes,
        bpm=bpm,
    )

    if result is None:
        print(
            "리듬을 분석하지 못했습니다."
        )
        sys.exit(1)

    print(
        "\n=== Rhythm Analysis ==="
    )

    print(
        f"Audio BPM: "
        f"{result['bpm']:.2f}"
    )

    print(
        f"1박 길이: "
        f"{result['beat_seconds']:.3f}s"
    )

    print(
        f"Best Grid: "
        f"{subdivision_name(result['best_subdivision'])}"
    )

    print(
        f"Best Offset: "
        f"{result['best_offset']:.3f}s"
    )

    print(
        f"평균 Grid 오차: "
        f"{result['average_error']:.3f}s"
    )

    print(
        f"최대 Grid 오차: "
        f"{result['max_error']:.3f}s"
    )

    # ---------------------------------
    # 6. 4분 / 8분 / 16분 Grid 비교
    # ---------------------------------

    print(
        "\n=== Grid Comparison ==="
    )

    for item in result["subdivision_results"]:
        print(
            f"{subdivision_name(item['subdivision']):6s}  "
            f"offset {item['offset']:.3f}s  "
            f"avg error {item['average_error']:.3f}s  "
            f"max error {item['max_error']:.3f}s"
        )

    # ---------------------------------
    # 7. 8분음표 Grid를 기준으로 사용
    # ---------------------------------

    eighth_result = get_subdivision_result(
        result,
        subdivision=2,
    )

    if eighth_result is None:
        print(
            "8분음표 Grid를 "
            "찾지 못했습니다."
        )
        sys.exit(1)

    eighth_offset = (
        eighth_result["offset"]
    )

    eighth_seconds = (
        eighth_result[
            "grid_seconds"
        ]
    )

    print(
        "\n=== 8th Note Grid ==="
    )

    print(
        f"Grid 간격: "
        f"{eighth_seconds:.3f}s"
    )

    print(
        f"Grid offset: "
        f"{eighth_offset:.3f}s"
    )

    # ---------------------------------
    # 8. 멜로디를 8분음표 Grid에 매핑
    # ---------------------------------

    mapped_notes = map_notes_to_grid(
        notes=notes,
        bpm=bpm,
        offset=eighth_offset,
        subdivision=2,
    )

    print(
        "\n=== Melody Grid Mapping ==="
    )

    for note in mapped_notes:
        print(
            f"{note['note']:4s}  "
            f"{note['start']:6.3f}s  "
            f"→ grid #{note['grid_index']:2d}  "
            f"{note['grid_start']:6.3f}s  "
            f"error {note['start_error']:+.3f}s"
        )

    # ---------------------------------
    # 9. 노트 간격 진단
    # ---------------------------------

    print(
        "\n=== Note Gap Analysis ==="
    )

    for i, note in enumerate(mapped_notes):
        print(
            f"{note['note']:4s}  "
            f"start {note['start']:.3f}s  "
            f"end {note['end']:.3f}s",
            end=""
        )

        if i < len(mapped_notes) - 1:
            next_note = (
                mapped_notes[i + 1]
            )

            start_gap = (
                next_note["start"]
                - note["start"]
            )

            silence = (
                next_note["start"]
                - note["end"]
            )

            grid_gap = (
                next_note["grid_index"]
                - note["grid_index"]
            )

            print(
                f"  | next-start "
                f"{start_gap:.3f}s"
                f"  | silence "
                f"{silence:.3f}s"
                f"  | grid-gap "
                f"{grid_gap}"
            )

        else:
            print()

    # ---------------------------------
    # 10. 프레이즈 분석
    # ---------------------------------

    phrases = detect_phrases(
        notes=mapped_notes,
        bpm=bpm,
        subdivision=2,
        min_silence_grids=1,
    )

    print(
        "\n=== Phrase Analysis ==="
    )

    for phrase in phrases:
        print(
            f"\nPhrase "
            f"{phrase['phrase']}  "
            f"{phrase['start']:.3f}s "
            f"- "
            f"{phrase['end']:.3f}s"
        )

        if (
            "silence_before"
            in phrase
        ):
            print(
                f"  이전 프레이즈와 무음: "
                f"{phrase['silence_before']:.3f}s"
            )

        for note in phrase["notes"]:
            print(
                f"  grid "
                f"#{note['grid_index']:2d}  "
                f"{note['note']:4s}  "
                f"{note['start']:.3f}s"
            )

    # ---------------------------------
    # 11. Quantize 미리보기
    # ---------------------------------

    quantized_notes = quantize_notes_to_grid(
        notes=notes,
        bpm=bpm,
        offset=eighth_offset,
        subdivision=2,
        strength=quantize_strength,
    )

    print(
        "\n=== Quantize Preview ==="
    )

    print(
        f"Strength: "
        f"{quantize_strength:.2f}"
    )

    for note in quantized_notes:
        print(
            f"{note['note']:4s}  "
            f"original "
            f"{note['original_start']:.3f}s  "
            f"→ grid "
            f"{note['target_grid_start']:.3f}s  "
            f"→ quantized "
            f"{note['quantized_start']:.3f}s  "
            f"move "
            f"{note['quantize_move']:+.3f}s"
        )


if __name__ == "__main__":
    main()