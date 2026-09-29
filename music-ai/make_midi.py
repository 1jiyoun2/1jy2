import argparse
from pathlib import Path

from src.audio_loader import load_audio
from src.tempo_detector import detect_tempo
from src.drum_midi import create_drum_midi


def parse_args():
    parser = argparse.ArgumentParser(
        description="분리된 드럼 stem을 하나의 MIDI 파일로 변환합니다."
    )

    parser.add_argument(
        "--source",
        required=True,
        help="BPM 분석에 사용할 원본 음원 경로"
    )

    parser.add_argument(
        "--stem",
        action="append",
        required=True,
        help=(
            "MIDI로 변환할 stem. "
            "형식: 악기명=파일경로 "
            "예: --stem kick=output/kick.wav"
        )
    )

    parser.add_argument(
        "--output",
        default="output/drums.mid",
        help="생성할 MIDI 파일 경로"
    )

    return parser.parse_args()


def parse_stems(stem_args):
    stem_paths = {}

    for item in stem_args:
        if "=" not in item:
            raise ValueError(
                f"잘못된 stem 형식: {item}\n"
                "예: --stem kick=output/kick.wav"
            )

        name, path = item.split("=", 1)

        name = name.strip()
        path = path.strip()

        if not name:
            raise ValueError("stem 악기명이 비어 있습니다.")

        stem_path = Path(path)

        if not stem_path.exists():
            raise FileNotFoundError(
                f"stem 파일을 찾을 수 없습니다: {stem_path}"
            )

        stem_paths[name] = str(stem_path)

    return stem_paths


def main():
    args = parse_args()

    source_path = Path(args.source)

    if not source_path.exists():
        raise FileNotFoundError(
            f"원본 음원을 찾을 수 없습니다: {source_path}"
        )

    stem_paths = parse_stems(args.stem)

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"\n원본 음원: {source_path}")
    print("사용할 stem:")

    for name, path in stem_paths.items():
        print(f"  {name}: {path}")

    print("\nBPM 분석 중...")

    y, sr = load_audio(source_path)
    bpm, _ = detect_tempo(y, sr)

    print(f"BPM: {bpm:.2f}")

    print("\nMIDI 생성 중...")

    create_drum_midi(
        stem_paths=stem_paths,
        output_path=str(output_path),
        bpm=bpm
    )

    print(f"\nMIDI 생성 완료: {output_path}")


if __name__ == "__main__":
    main()