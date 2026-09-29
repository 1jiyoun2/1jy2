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


MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]


def detect_melody_key(notes):
    """
    검출된 멜로디 노트들의 음높이와 길이를 이용해
    가장 가능성이 높은 Major / Minor Key를 찾는다.
    """

    histogram = np.zeros(12)

    for note in notes:
        pitch_class = note["midi"] % 12
        duration = note["duration"]

        histogram[pitch_class] += duration

    if histogram.sum() == 0:
        return None

    scores = []

    for root in range(12):

        major_score = np.corrcoef(
            histogram,
            np.roll(MAJOR_PROFILE, root)
        )[0, 1]

        minor_score = np.corrcoef(
            histogram,
            np.roll(MINOR_PROFILE, root)
        )[0, 1]

        scores.append(
            (
                major_score,
                root,
                "major"
            )
        )

        scores.append(
            (
                minor_score,
                root,
                "minor"
            )
        )

    best = max(
        scores,
        key=lambda item: item[0]
    )

    _, root, mode = best

    return {
        "root": root,
        "mode": mode,
        "name": f"{NOTE_NAMES[root]} {mode}"
    }


def create_diatonic_chords(key):
    """
    Key 안에서 사용할 7개의 기본 3화음을 만든다.
    """

    root = key["root"]

    if key["mode"] == "major":
        scale = MAJOR_SCALE
    else:
        scale = MINOR_SCALE

    scale_notes = [
        (root + interval) % 12
        for interval in scale
    ]

    chords = []

    for degree in range(7):

        chord = [
            scale_notes[degree],
            scale_notes[(degree + 2) % 7],
            scale_notes[(degree + 4) % 7],
        ]

        chords.append({
            "degree": degree + 1,
            "notes": chord
        })

    return chords


def choose_chord(
    segment_notes,
    chords
):
    """
    한 구간의 멜로디와 가장 잘 맞는 코드를 선택한다.
    """

    best_chord = None
    best_score = -1

    for chord in chords:

        score = 0

        for note in segment_notes:
            pitch_class = (
                note["midi"] % 12
            )

            if pitch_class in chord["notes"]:
                score += note["duration"]

        if score > best_score:
            best_score = score
            best_chord = chord

    return best_chord


def create_chord_progression(
    notes,
    key,
    chord_seconds=2.0
):
    """
    첫 멜로디가 시작되는 시점부터
    일정 시간 단위로 화음을 만든다.
    """

    if not notes:
        return []

    chords = create_diatonic_chords(
        key
    )

    # 첫 멜로디 시작 시점
    song_start = min(
        note["start"]
        for note in notes
    )

    # 마지막 멜로디 종료 시점
    song_end = max(
        note["end"]
        for note in notes
    )

    progression = []

    start = song_start

    while start < song_end:

        end = min(
            start + chord_seconds,
            song_end
        )

        segment_notes = []

        for note in notes:
            if (
                note["start"] < end
                and note["end"] > start
            ):
                segment_notes.append(
                    note
                )

        if segment_notes:
            chord = choose_chord(
                segment_notes,
                chords
            )

            progression.append({
                "start": start,
                "end": end,
                "degree": chord["degree"],
                "notes": chord["notes"],
            })

        start = end

    return progression