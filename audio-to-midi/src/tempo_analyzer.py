import librosa


def analyze_tempo(y, sr):
    tempo, beat_frames = librosa.beat.beat_track(
        y=y,
        sr=sr,
    )

    bpm = float(tempo.item())

    beat_times = librosa.frames_to_time(
        beat_frames,
        sr=sr,
    )

    return {
        "bpm": bpm,
        "beat_frames": beat_frames,
        "beat_times": beat_times,
    }