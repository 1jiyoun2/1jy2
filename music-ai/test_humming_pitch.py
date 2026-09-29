import sys
from pathlib import Path

from src.audio_loader import load_audio
from src.humming_pitch import detect_pitch, group_pitch_to_notes


if len(sys.argv) < 2:
    print("사용법: python test_humming_pitch.py <허밍파일>")
    sys.exit(1)


audio_path = Path(sys.argv[1])

if not audio_path.exists():
    print(f"파일을 찾을 수 없습니다: {audio_path}")
    sys.exit(1)


y, sr = load_audio(audio_path)

results = detect_pitch(y, sr)

print(f"\n검출된 프레임 수: {len(results)}")
print("\n처음 30개 결과:")

for item in results[:30]:
    print(
        f"{item['time']:6.2f}s  "
        f"{item['frequency']:8.2f} Hz  "
        f"MIDI {item['midi']:6.2f}  "
        f"confidence {item['confidence']:.2f}"
    )

notes = group_pitch_to_notes(results)

print("\n=== 검출된 멜로디 노트 ===")

for note in notes:
    print(
        f"{note['start']:6.2f}s - "
        f"{note['end']:6.2f}s  "
        f"{note['note']:4s}  "
        f"MIDI {note['midi']:3d}  "
        f"({note['duration']:.2f}s)"
    )