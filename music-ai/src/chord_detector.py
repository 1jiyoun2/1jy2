import librosa
import numpy as np


NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


def create_chord_templates():
    chord_templates = {}

    for root in range(12):
        major = np.zeros(12)
        minor = np.zeros(12)

        major[root] = 1
        major[(root + 4) % 12] = 1
        major[(root + 7) % 12] = 1

        minor[root] = 1
        minor[(root + 3) % 12] = 1
        minor[(root + 7) % 12] = 1

        chord_templates[NOTE_NAMES[root]] = major
        chord_templates[NOTE_NAMES[root] + "m"] = minor

    return chord_templates


def detect_chords(y, sr, beat_frames, duration):
    chroma = librosa.feature.chroma_cqt(
        y=y,
        sr=sr
    )

    chord_templates = create_chord_templates()

    chord_results = []

    for i in range(len(beat_frames) - 1):
        start_frame = beat_frames[i]
        end_frame = beat_frames[i + 1]

        segment = chroma[:, start_frame:end_frame]

        if segment.shape[1] == 0:
            continue

        segment_chroma = segment.mean(axis=1)

        best_chord = None
        best_score = -1

        for chord_name, template in chord_templates.items():
            score = np.dot(
                segment_chroma,
                template
            )

            if score > best_score:
                best_score = score
                best_chord = chord_name

        time = librosa.frames_to_time(
            start_frame,
            sr=sr
        )

        chord_results.append(
            (time, best_chord)
        )

    return merge_chords(
        chord_results,
        duration
    )


def merge_chords(chord_results, duration):
    merged = []

    for time, chord in chord_results:
        if not merged or merged[-1][1] != chord:
            merged.append([time, chord])

    result = []

    for i in range(len(merged)):
        start_time = merged[i][0]
        chord = merged[i][1]

        if i < len(merged) - 1:
            end_time = merged[i + 1][0]
        else:
            end_time = duration

        result.append(
            (start_time, end_time, chord)
        )

    return result