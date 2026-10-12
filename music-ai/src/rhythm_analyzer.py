import numpy as np


def get_beat_seconds(bpm):
    return 60.0 / bpm


def get_grid_seconds(bpm, subdivision):
    return get_beat_seconds(bpm) / subdivision


def get_grid_step_beats(subdivision):
    return 1.0 / subdivision


def find_best_grid_offset(
    notes,
    bpm,
    subdivision=4,
    search_steps=200,
):
    if not notes:
        return 0.0

    grid_seconds = get_grid_seconds(
        bpm,
        subdivision,
    )

    starts = np.array(
        [note["start"] for note in notes],
        dtype=float,
    )

    offsets = np.linspace(
        0.0,
        grid_seconds,
        search_steps,
        endpoint=False,
    )

    best_offset = 0.0
    best_error = float("inf")

    for offset in offsets:
        errors = []

        for start in starts:
            grid_index = round(
                (start - offset) / grid_seconds
            )

            nearest_grid = (
                offset
                + grid_index * grid_seconds
            )

            errors.append(
                abs(start - nearest_grid)
            )

        average_error = float(
            np.mean(errors)
        )

        if average_error < best_error:
            best_error = average_error
            best_offset = float(offset)

    return best_offset


def analyze_subdivision(
    notes,
    bpm,
    subdivision,
):
    offset = find_best_grid_offset(
        notes=notes,
        bpm=bpm,
        subdivision=subdivision,
    )

    grid_seconds = get_grid_seconds(
        bpm,
        subdivision,
    )

    errors = []

    for note in notes:
        grid_index = round(
            (note["start"] - offset)
            / grid_seconds
        )

        nearest = (
            offset
            + grid_index * grid_seconds
        )

        errors.append(
            abs(note["start"] - nearest)
        )

    return {
        "subdivision": subdivision,
        "offset": offset,
        "grid_seconds": grid_seconds,
        "average_error": float(np.mean(errors)),
        "max_error": float(np.max(errors)),
    }


def analyze_rhythm(
    notes,
    bpm,
):
    if not notes:
        return None

    results = []

    for subdivision in (1, 2, 4):
        results.append(
            analyze_subdivision(
                notes=notes,
                bpm=bpm,
                subdivision=subdivision,
            )
        )

    best = min(
        results,
        key=lambda item: item["average_error"],
    )

    return {
        "bpm": float(bpm),
        "beat_seconds": get_beat_seconds(bpm),
        "best_subdivision": best["subdivision"],
        "best_offset": best["offset"],
        "average_error": best["average_error"],
        "max_error": best["max_error"],
        "subdivision_results": results,
    }


def get_subdivision_result(
    rhythm_result,
    subdivision,
):
    for result in rhythm_result["subdivision_results"]:
        if result["subdivision"] == subdivision:
            return result

    return None


def seconds_to_beats(
    seconds,
    bpm,
    offset,
):
    beat_seconds = get_beat_seconds(bpm)

    return (
        seconds - offset
    ) / beat_seconds


def beats_to_seconds(
    beats,
    bpm,
    offset,
):
    beat_seconds = get_beat_seconds(bpm)

    return (
        offset
        + beats * beat_seconds
    )


def quantize_beat(
    beat,
    subdivision,
    strength=1.0,
):
    step = get_grid_step_beats(
        subdivision
    )

    target = (
        round(beat / step)
        * step
    )

    return (
        beat
        + (target - beat) * strength
    )


def quantize_notes_to_beats(
    notes,
    bpm,
    offset,
    subdivision=4,
    strength=1.0,
):
    """
    노트의 시작점과 끝점을 모두 Beat Grid에 맞춘다.

    subdivision=4:
        1박을 4칸으로 나누므로
        16분음표 해상도.

    strength=1.0:
        완전 Quantize.

    strength=0.75:
        Grid까지 거리의 75%만 이동.
    """

    if not notes:
        return []

    step = get_grid_step_beats(
        subdivision
    )

    quantized_notes = []

    for note in notes:
        original_start_beat = seconds_to_beats(
            note["start"],
            bpm,
            offset,
        )

        original_end_beat = seconds_to_beats(
            note["end"],
            bpm,
            offset,
        )

        quantized_start_beat = quantize_beat(
            original_start_beat,
            subdivision,
            strength,
        )

        quantized_end_beat = quantize_beat(
            original_end_beat,
            subdivision,
            strength,
        )

        minimum_end = (
            quantized_start_beat
            + step
        )

        if quantized_end_beat < minimum_end:
            quantized_end_beat = minimum_end

        start_seconds = beats_to_seconds(
            quantized_start_beat,
            bpm,
            offset,
        )

        end_seconds = beats_to_seconds(
            quantized_end_beat,
            bpm,
            offset,
        )

        quantized_notes.append({
            **note,
            "original_start": note["start"],
            "original_end": note["end"],
            "beat_start": quantized_start_beat,
            "beat_end": quantized_end_beat,
            "beat_duration": (
                quantized_end_beat
                - quantized_start_beat
            ),
            "start": start_seconds,
            "end": end_seconds,
        })

    return quantized_notes


def detect_phrases(
    notes,
    bpm,
    min_silence_beats=0.5,
):
    """
    실제 노트 사이의 쉼을 Beat 단위로 계산한다.

    기본값 0.5:
        반 박 이상 실제 쉼이 있으면
        새로운 프레이즈 후보로 판단.
    """

    if not notes:
        return []

    beat_seconds = get_beat_seconds(
        bpm
    )

    phrases = []
    current_notes = [notes[0]]

    for index in range(
        len(notes) - 1
    ):
        current_note = notes[index]
        next_note = notes[index + 1]

        silence_seconds = (
            next_note["original_start"]
            - current_note["original_end"]
        )

        silence_beats = (
            silence_seconds
            / beat_seconds
        )

        if silence_beats >= min_silence_beats:
            phrases.append({
                "notes": current_notes,
                "silence_after_beats": silence_beats,
            })

            current_notes = [
                next_note
            ]
        else:
            current_notes.append(
                next_note
            )

    phrases.append({
        "notes": current_notes,
        "silence_after_beats": None,
    })

    for index, phrase in enumerate(phrases):
        phrase["phrase"] = index + 1
        phrase["start_beat"] = (
            phrase["notes"][0]["beat_start"]
        )
        phrase["end_beat"] = (
            phrase["notes"][-1]["beat_end"]
        )

    return phrases