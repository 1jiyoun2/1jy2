from pathlib import Path
import subprocess
import tempfile

import librosa


SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".aac",
    ".ogg",
}


def convert_to_analysis_wav(
    input_path,
    output_path,
    sample_rate=44100,
):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-vn",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg 오디오 변환에 실패했습니다.\n"
            + result.stderr
        )


def load_audio(
    audio_path,
    target_sr=44100,
):
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {audio_path}"
        )

    extension = audio_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 오디오 형식입니다: {extension}"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_wav = (
            Path(temp_dir)
            / "analysis.wav"
        )

        convert_to_analysis_wav(
            input_path=audio_path,
            output_path=temp_wav,
            sample_rate=target_sr,
        )

        y, sr = librosa.load(
            temp_wav,
            sr=None,
            mono=True,
        )

    return y, sr


def get_audio_info(
    y,
    sr,
):
    duration = (
        len(y) / sr
    )

    return {
        "sample_rate": sr,
        "samples": len(y),
        "duration": duration,
    }