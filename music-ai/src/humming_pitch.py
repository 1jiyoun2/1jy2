import librosa
import numpy as np


def detect_pitch(y, sr):
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    times = librosa.times_like(
        f0,
        sr=sr
    )

    result = []

    for time, frequency, voiced, probability in zip(
        times,
        f0,
        voiced_flag,
        voiced_prob
    ):
        if not voiced:
            continue

        if np.isnan(frequency):
            continue

        if probability < 0.5:  # 테스트 후 추가 부분
            continue

        midi_note = librosa.hz_to_midi(
            frequency
        )

        result.append({
            "time": float(time),
            "frequency": float(frequency),
            "midi": float(midi_note),
            "confidence": float(probability),
        })

    return result

def group_pitch_to_notes(
    pitch_frames,
    pitch_tolerance=0.65,
    max_gap=0.08,
    min_duration=0.08
):
    """
    프레임 단위 피치 결과를 실제 음표 단위로 묶는다.

    pitch_tolerance:
        같은 음으로 인정할 최대 반음 차이

    max_gap:
        프레임 사이가 이 시간 이상 벌어지면
        새로운 음으로 본다.

    min_duration:
        이보다 짧은 음은 잡음으로 보고 제거한다.
    """

    if not pitch_frames:
        return []

    notes = []

    current_frames = [pitch_frames[0]]

    for frame in pitch_frames[1:]:

        previous_time = current_frames[-1]["time"]

        current_pitches = [
            item["midi"]
            for item in current_frames
        ]

        center_pitch = float(
            np.median(current_pitches)
        )

        time_gap = (
            frame["time"] - previous_time
        )

        pitch_difference = abs(
            frame["midi"] - center_pitch
        )

        # 같은 음으로 판단
        if (
            time_gap <= max_gap
            and pitch_difference <= pitch_tolerance
        ):
            current_frames.append(frame)

        else:
            _append_note(
                notes,
                current_frames,
                min_duration
            )

            current_frames = [frame]

    # 마지막 음 처리
    _append_note(
        notes,
        current_frames,
        min_duration
    )

    return notes


def _append_note(
    notes,
    frames,
    min_duration
):
    if not frames:
        return

    start_time = frames[0]["time"]
    end_time = frames[-1]["time"]

    duration = end_time - start_time

    if duration < min_duration:
        return

    midi_values = [
        frame["midi"]
        for frame in frames
    ]

    median_midi = float(
        np.median(midi_values)
    )

    # 최종적으로 가장 가까운 MIDI 음으로 맞춤
    midi_note = int(
        np.floor(median_midi + 0.5)
    )

    note_name = librosa.midi_to_note(
        midi_note,
        octave=True
    )

    notes.append({
        "start": start_time,
        "end": end_time,
        "duration": duration,
        "midi": midi_note,
        "note": note_name,
        "pitch": median_midi,
    })

def smooth_note_lengths(
    notes,
    max_gap=0.20,
    fill_ratio=0.85
):
    """
    가까운 다음 음까지의 짧은 공백을 줄여
    MIDI가 너무 끊겨 들리지 않도록 한다.

    max_gap:
        이보다 짧은 공백만 연결 대상으로 본다.

    fill_ratio:
        공백의 몇 %까지 현재 음을 늘릴지 결정한다.
    """

    if not notes:
        return []

    smoothed = [
        note.copy()
        for note in notes
    ]

    for i in range(len(smoothed) - 1):
        current = smoothed[i]
        next_note = smoothed[i + 1]

        gap = (
            next_note["start"]
            - current["end"]
        )

        if 0 < gap <= max_gap:
            current["end"] += (
                gap * fill_ratio
            )

            current["duration"] = (
                current["end"]
                - current["start"]
            )

    return smoothed