import librosa


def detect_tempo(y, sr):
    tempo, beat_frames = librosa.beat.beat_track(
        y=y,
        sr=sr
    )

    bpm = tempo.item()

    return bpm, beat_frames