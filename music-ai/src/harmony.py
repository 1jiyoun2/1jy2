import numpy as np


NOTE_NAMES = [
    "C",
    "C♯",
    "D",
    "D♯",
    "E",
    "F",
    "F♯",
    "G",
    "G♯",
    "A",
    "A♯",
    "B",
]


MAJOR_PROFILE = np.array([
    6.35,
    2.23,
    3.48,
    2.33,
    4.38,
    4.09,
    2.52,
    5.19,
    2.39,
    3.66,
    2.29,
    2.88,
])


MINOR_PROFILE = np.array([
    6.33,
    2.68,
    3.52,
    5.38,
    2.60,
    3.53,
    2.54,
    4.75,
    3.98,
    2.69,
    3.34,
    3.17,
])


MAJOR_SCALE = [
    0,
    2,
    4,
    5,
    7,
    9,
    11,
]


MINOR_SCALE = [
    0,
    2,
    3,
    5,
    7,
    8,
    10,
]


MAJOR_TRIADS = [
    (0, 4, 7),
    (2, 5, 9),
    (4, 7, 11),
    (5, 9, 0),
    (7, 11, 2),
    (9, 0, 4),
]


MINOR_TRIADS = [
    (0, 3, 7),
    (2, 5, 8),
    (3, 7, 10),
    (5, 8, 0),
    (7, 10, 2),
    (8, 0, 3),
]


def rotate_profile(
    profile,
    tonic,
):
    return np.roll(
        profile,
        tonic,
    )


def detect_melody_key(notes):
    if not notes:
        return None

    histogram = np.zeros(
        12,
        dtype=float,
    )

    for note in notes:
        pitch_class = (
            note["midi"]
            % 12
        )

        if (
            "beat_duration"
            in note
        ):
            weight = max(
                note["beat_duration"],
                0.25,
            )
        else:
            weight = max(
                note["end"]
                - note["start"],
                0.05,
            )

        histogram[pitch_class] += weight

    if histogram.sum() == 0:
        return None

    best_score = float(
        "-inf"
    )

    best_key = None

    for tonic in range(12):
        major_score = np.corrcoef(
            histogram,
            rotate_profile(
                MAJOR_PROFILE,
                tonic,
            ),
        )[0, 1]

        minor_score = np.corrcoef(
            histogram,
            rotate_profile(
                MINOR_PROFILE,
                tonic,
            ),
        )[0, 1]

        if major_score > best_score:
            best_score = major_score
            best_key = {
                "tonic": tonic,
                "mode": "major",
                "name": (
                    f"{NOTE_NAMES[tonic]} major"
                ),
            }

        if minor_score > best_score:
            best_score = minor_score
            best_key = {
                "tonic": tonic,
                "mode": "minor",
                "name": (
                    f"{NOTE_NAMES[tonic]} minor"
                ),
            }

    return best_key


def create_diatonic_chords(key):
    tonic = key["tonic"]

    if key["mode"] == "major":
        scale = MAJOR_SCALE
        templates = MAJOR_TRIADS
    else:
        scale = MINOR_SCALE
        templates = MINOR_TRIADS

    chords = []

    for degree, template in enumerate(
        templates
    ):
        notes = [
            (tonic + pitch)
            % 12
            for pitch in template
        ]

        root = (
            tonic
            + scale[degree]
        ) % 12

        chords.append({
            "degree": degree + 1,
            "root": root,
            "notes": notes,
        })

    return chords


def get_note_overlap(
    note,
    start_beat,
    end_beat,
):
    overlap_start = max(
        note["beat_start"],
        start_beat,
    )

    overlap_end = min(
        note["beat_end"],
        end_beat,
    )

    return max(
        0.0,
        overlap_end - overlap_start,
    )


def score_chord(
    chord,
    notes,
    start_beat,
    end_beat,
):
    score = 0.0

    for note in notes:
        overlap = get_note_overlap(
            note,
            start_beat,
            end_beat,
        )

        if overlap <= 0:
            continue

        pitch_class = (
            note["midi"]
            % 12
        )

        if pitch_class in chord["notes"]:
            score += overlap * 2.0
        else:
            score -= overlap * 0.35

        if pitch_class == chord["root"]:
            score += overlap * 0.5

    return score


def choose_chord(
    notes,
    chords,
    start_beat,
    end_beat,
    previous_chord=None,
):
    best_chord = None
    best_score = float(
        "-inf"
    )

    for chord in chords:
        score = score_chord(
            chord,
            notes,
            start_beat,
            end_beat,
        )

        if previous_chord is not None:
            if (
                chord["degree"]
                == previous_chord["degree"]
            ):
                score += 0.1

        if score > best_score:
            best_score = score
            best_chord = chord

    return best_chord


def create_chord_progression(
    notes,
    key,
    bpm,
    offset,
    beats_per_chord=4.0,
):
    """
    화음을 초가 아닌 Beat 기준으로 만든다.

    beats_per_chord=4:
        기본적으로 4/4 한 마디마다
        코드 후보를 다시 선택한다.

    첫 멜로디 노트를 Beat 0 기준으로 삼아
    코드 타이밍이 파일 앞쪽 무음에 흔들리지 않게 한다.
    """

    if not notes:
        return []

    chords = create_diatonic_chords(
        key
    )

    first_beat = notes[0][
        "beat_start"
    ]

    last_beat = max(
        note["beat_end"]
        for note in notes
    )

    progression = []
    previous_chord = None

    segment_start = first_beat

    while segment_start < last_beat:
        segment_end = min(
            segment_start
            + beats_per_chord,
            last_beat,
        )

        chord = choose_chord(
            notes=notes,
            chords=chords,
            start_beat=segment_start,
            end_beat=segment_end,
            previous_chord=previous_chord,
        )

        if chord is None:
            break

        beat_seconds = (
            60.0 / bpm
        )

        start_seconds = (
            offset
            + segment_start
            * beat_seconds
        )

        end_seconds = (
            offset
            + segment_end
            * beat_seconds
        )

        progression.append({
            "start": start_seconds,
            "end": end_seconds,
            "start_beat": segment_start,
            "end_beat": segment_end,
            "degree": chord["degree"],
            "root": chord["root"],
            "notes": chord["notes"],
        })

        previous_chord = chord
        segment_start = segment_end

    return progression