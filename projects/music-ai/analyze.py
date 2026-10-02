from pathlib import Path
import sys

import librosa

from src.audio_loader import load_audio
from src.tempo_detector import detect_tempo
from src.key_detector import detect_key
from src.chord_detector import detect_chords


def print_menu():
    print("\n=== Music AI ===")
    print("1. BPM 분석")
    print("2. Key 분석")
    print("3. Chord 분석")
    print("4. 전체 분석")
    print("5. 종료")


if len(sys.argv) < 2:
    print("사용법: python analyze.py <음원파일경로>")
    sys.exit(1)

audio_path = Path(sys.argv[1])

if not audio_path.exists():
    print(f"파일을 찾을 수 없습니다: {audio_path}")
    sys.exit(1)

print(f"\n선택한 파일: {audio_path.name}")

# 음원은 처음 한 번만 읽어둠
y, sr = load_audio(audio_path)

duration = librosa.get_duration(y=y, sr=sr)


while True:
    print_menu()

    choice = input("\n선택: ").strip()

    if choice == "1":
        bpm, _ = detect_tempo(y, sr)

        print(f"\nBPM: {bpm:.2f}")

    elif choice == "2":
        key = detect_key(y, sr)

        print(f"\nKey: {key}")

    elif choice == "3":
        _, beat_frames = detect_tempo(y, sr)

        chords = detect_chords(
            y,
            sr,
            beat_frames,
            duration
        )

        print("\nChord progression:")

        for start, end, chord in chords:
            print(
                f"{start:6.2f}s - {end:6.2f}s  {chord}"
            )

    elif choice == "4":
        bpm, beat_frames = detect_tempo(y, sr)
        key = detect_key(y, sr)

        chords = detect_chords(
            y,
            sr,
            beat_frames,
            duration
        )

        print("\n=== 분석 결과 ===")
        print(f"BPM: {bpm:.2f}")
        print(f"Key: {key}")
        print(f"Sample Rate: {sr} Hz")
        print(f"Samples: {len(y)}")
        print(f"Duration: {duration:.2f} seconds")

        print("\nChord progression:")

        for start, end, chord in chords:
            print(
                f"{start:6.2f}s - {end:6.2f}s  {chord}"
            )

    elif choice == "5":
        print("\n종료합니다.")
        break

    else:
        print("\n잘못된 선택입니다. 1~5 중에서 선택하세요.")