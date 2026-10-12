from pathlib import Path
import argparse

from src.audio_loader import (
    load_audio,
    get_audio_info,
)

from src.tempo_analyzer import (
    analyze_tempo,
)

from src.stem_separator import (
    separate_stems,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="오디오 파일을 분석해 MIDI로 변환합니다."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="입력 오디오 파일 경로",
    )

    parser.add_argument(
        "--stem-output",
        default="output/stems",
        help="Stem 분리 결과 저장 폴더",
    )

    parser.add_argument(
        "--stem-model",
        default="htdemucs",
        help="Demucs 모델 이름",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(
            f"파일을 찾을 수 없습니다: "
            f"{input_path}"
        )
        return

    print(
        f"\n입력 파일: "
        f"{input_path}"
    )

    # ---------------------------------
    # 1. 오디오 로드
    # ---------------------------------

    print(
        "\n오디오 로드 중..."
    )

    try:
        y, sr = load_audio(
            input_path
        )

    except Exception as error:
        print(
            f"오디오 로드 실패: "
            f"{error}"
        )
        return

    info = get_audio_info(
        y,
        sr,
    )

    print(
        "\n=== Audio Info ==="
    )

    print(
        f"Sample Rate: "
        f"{info['sample_rate']} Hz"
    )

    print(
        f"Samples: "
        f"{info['samples']}"
    )

    print(
        f"Duration: "
        f"{info['duration']:.2f} sec"
    )

    # ---------------------------------
    # 2. Tempo 분석
    # ---------------------------------

    print(
        "\nTempo 분석 중..."
    )

    tempo_result = analyze_tempo(
        y,
        sr,
    )

    print(
        "\n=== Tempo Analysis ==="
    )

    print(
        f"BPM: "
        f"{tempo_result['bpm']:.2f}"
    )

    print(
        f"Detected Beats: "
        f"{len(tempo_result['beat_times'])}"
    )

    print(
        "\n=== Beat Preview ==="
    )

    for index, beat_time in enumerate(
        tempo_result["beat_times"][:20],
        start=1,
    ):
        print(
            f"Beat {index:2d}: "
            f"{beat_time:.3f} sec"
        )

    # ---------------------------------
    # 3. Stem 분리
    # ---------------------------------

    print(
        "\nStem 분리 중..."
    )

    try:
        stem_paths = separate_stems(
            input_path=input_path,
            output_dir=args.stem_output,
            model=args.stem_model,
        )

    except Exception as error:
        print(
            f"Stem 분리 실패: "
            f"{error}"
        )
        return

    print(
        "\n=== Stem Files ==="
    )

    for name, path in stem_paths.items():
        print(
            f"{name:7s}: "
            f"{path}"
        )

    print(
        "\nStem 분리 완료"
    )


if __name__ == "__main__":
    main()