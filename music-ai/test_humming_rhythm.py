import sys
from pathlib import Path

from src.audio_loader import load_audio

from src.humming_pitch import (
    detect_pitch,
    group_pitch_to_notes,
    smooth_note_lengths,
)

from src.rhythm_analyzer import (
    analyze_rhythm,
)


def main():
    if len(sys.argv) < 2:
        print(
            "사용법: "
            "python test_humming_rhythm.py <허밍파일>"
        )
        sys.exit(1)

    audio_path = Path(
        sys.argv[1]
    )

    if not audio_path.exists():
        print(
            f"파일을 찾을 수 없습니다: "
            f"{audio_path}"
        )
        sys.exit(1)

    print(
        f"\n허밍 파일: "
        f"{audio_path}"
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
    # 2. 피치 검출
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
    # 3. 프레임 → 멜로디 노트
    # ---------------------------------

    notes = group_pitch_to_notes(
        pitch_frames
    )

    notes = smooth_note_lengths(
        notes
    )

    if not notes:
        print(
            "유효한 멜로디 노트를 "
            "검출하지 못했습니다."
        )
        sys.exit(1)

    print(
        f"검출된 멜로디 노트: "
        f"{len(notes)}개"
    )

    # ---------------------------------
    # 4. 리듬 분석
    # ---------------------------------

    print(
        "\n리듬 분석 중..."
    )

    result = analyze_rhythm(
        notes,
        min_bpm=60,
        max_bpm=180,
        subdivision=2,
    )

    if result is None:
        print(
            "리듬을 분석하지 못했습니다."
        )
        sys.exit(1)

    # ---------------------------------
    # 5. BPM 결과
    # ---------------------------------

    print(
        "\n=== Rhythm Analysis ==="
    )

    print(
        f"Estimated BPM: "
        f"{result['bpm']:.2f}"
    )

    print(
        f"Grid offset: "
        f"{result['offset']:.3f}s"
    )

    print(
        f"Grid subdivision: "
        f"1/{result['subdivision'] * 4}"
    )

    # ---------------------------------
    # 6. BPM 후보 출력
    # ---------------------------------

    print(
        "\n=== BPM Candidates ==="
    )

    for candidate in result["candidates"]:
        print(
            f"{candidate['bpm']:7.2f} BPM  "
            f"support {candidate['count']}"
        )

    # ---------------------------------
    # 7. Melody vs Grid 비교
    # ---------------------------------

    print(
        "\n=== Melody / Nearest Grid ==="
    )

    grid = result["grid"]

    total_error = 0.0

    for note in notes:
        start = note["start"]

        nearest = min(
            grid,
            key=lambda value: abs(
                value - start
            )
        )

        error = (
            start - nearest
        )

        total_error += abs(
            error
        )

        print(
            f"{note['note']:4s}  "
            f"{start:6.3f}s  "
            f"→ grid {nearest:6.3f}s  "
            f"error {error:+.3f}s"
        )

    average_error = (
        total_error
        / len(notes)
    )

    print(
        "\n평균 Grid 오차: "
        f"{average_error:.3f}s"
    )

    # ---------------------------------
    # 8. Grid 일부 출력
    # ---------------------------------

    print(
        "\n=== Grid Preview ==="
    )

    for value in grid[:20]:
        print(
            f"{value:.3f}s"
        )


if __name__ == "__main__":
    main()