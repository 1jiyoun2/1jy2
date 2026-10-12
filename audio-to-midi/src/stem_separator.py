from pathlib import Path
import subprocess


DEFAULT_MODEL = "htdemucs"


def separate_stems(
    input_path,
    output_dir,
    model=DEFAULT_MODEL,
):
    """
    Demucs를 사용해 오디오를 stem으로 분리한다.

    Parameters
    ----------
    input_path : str 또는 Path
        입력 오디오 파일 경로

    output_dir : str 또는 Path
        Demucs 결과를 저장할 기준 폴더

    model : str
        사용할 Demucs 모델 이름
        기본값은 htdemucs

    Returns
    -------
    dict
        vocals, drums, bass, other 파일 경로
    """

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"입력 파일을 찾을 수 없습니다: {input_path}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "demucs",
        "-n",
        model,
        "-o",
        str(output_dir),
        str(input_path),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Demucs stem 분리에 실패했습니다.\n"
            + result.stdout
        )

    track_name = input_path.stem

    result_dir = (
        output_dir
        / model
        / track_name
    )

    if not result_dir.exists():
        raise RuntimeError(
            "Demucs 실행은 완료되었지만 "
            f"결과 폴더를 찾을 수 없습니다: {result_dir}"
        )

    stem_paths = {
        "vocals": result_dir / "vocals.wav",
        "drums": result_dir / "drums.wav",
        "bass": result_dir / "bass.wav",
        "other": result_dir / "other.wav",
    }

    missing = [
        name
        for name, path in stem_paths.items()
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "다음 stem 파일을 찾을 수 없습니다: "
            + ", ".join(missing)
        )

    return stem_paths