import librosa
import numpy as np


NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

MAJOR_PROFILE = np.array([
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88
])

MINOR_PROFILE = np.array([
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17
])


def detect_key(y, sr):
    chroma = librosa.feature.chroma_cqt(
        y=y,
        sr=sr
    )

    chroma_mean = chroma.mean(axis=1)

    scores = []

    for i in range(12):
        major_score = np.corrcoef(
            chroma_mean,
            np.roll(MAJOR_PROFILE, i)
        )[0, 1]

        minor_score = np.corrcoef(
            chroma_mean,
            np.roll(MINOR_PROFILE, i)
        )[0, 1]

        scores.append(
            (major_score, f"{NOTE_NAMES[i]} major")
        )

        scores.append(
            (minor_score, f"{NOTE_NAMES[i]} minor")
        )

    best_key = max(
        scores,
        key=lambda x: x[0]
    )

    return best_key[1]