import subprocess
import tempfile

import librosa


def load_audio(audio_path):
    with tempfile.NamedTemporaryFile(suffix=".wav") as temp_wav:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(audio_path),
                "-ac", "1",
                "-ar", "44100",
                temp_wav.name,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        y, sr = librosa.load(temp_wav.name, sr=None)

    return y, sr