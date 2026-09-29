import numpy as np


def estimate_bpm_candidates(
    notes,
    min_bpm=60,
    max_bpm=180
):
    """
    멜로디 노트의 시작 시점 간격을 이용해서
    BPM 후보들을 계산한다.
    """

    if len(notes) < 2:
        return []

    starts = np.array(
        [note["start"] for note in notes],
        dtype=float
    )

    intervals = np.diff(starts)

    # 너무 짧거나 너무 긴 간격 제거
    intervals = intervals[
        (intervals >= 0.10)
        & (intervals <= 2.0)
    ]

    if len(intervals) == 0:
        return []

    candidates = []

    for interval in intervals:
        bpm = 60.0 / interval

        # 같은 리듬이 배속/반속으로 해석될 가능성도 고려
        variants = [
            bpm,
            bpm / 2,
            bpm * 2,
        ]

        for candidate in variants:
            if min_bpm <= candidate <= max_bpm:
                candidates.append(
                    float(candidate)
                )

    candidates.sort()

    return candidates


def cluster_bpm_candidates(
    candidates,
    tolerance=3.0
):
    """
    비슷한 BPM 후보들을 그룹으로 묶는다.
    """

    if not candidates:
        return []

    groups = []

    for bpm in candidates:
        placed = False

        for group in groups:
            center = np.mean(group)

            if abs(bpm - center) <= tolerance:
                group.append(bpm)
                placed = True
                break

        if not placed:
            groups.append([bpm])

    ranked = []

    for group in groups:
        ranked.append({
            "bpm": float(np.mean(group)),
            "count": len(group),
        })

    ranked.sort(
        key=lambda item: item["count"],
        reverse=True
    )

    return ranked


def find_best_grid_offset(
    notes,
    bpm,
    subdivision=2
):
    """
    BPM이 주어졌을 때,
    멜로디 시작점들이 가장 잘 맞는
    grid 시작 위치(offset)를 찾는다.

    subdivision=2:
        8분음표 단위 grid
    """

    if not notes:
        return 0.0

    beat_seconds = 60.0 / bpm
    grid_seconds = beat_seconds / subdivision

    starts = np.array(
        [note["start"] for note in notes],
        dtype=float
    )

    offsets = np.linspace(
        0,
        grid_seconds,
        100,
        endpoint=False
    )

    best_offset = 0.0
    best_score = float("inf")

    for offset in offsets:
        total_error = 0.0

        for start in starts:
            grid_index = round(
                (start - offset)
                / grid_seconds
            )

            nearest_grid = (
                offset
                + grid_index * grid_seconds
            )

            total_error += abs(
                start - nearest_grid
            )

        if total_error < best_score:
            best_score = total_error
            best_offset = offset

    return float(best_offset)


def create_grid(
    notes,
    bpm,
    offset,
    subdivision=2
):
    """
    멜로디 전체 구간에 대한
    subdivision grid를 생성한다.
    """

    if not notes:
        return []

    beat_seconds = 60.0 / bpm
    grid_seconds = beat_seconds / subdivision

    end_time = max(
        note["end"]
        for note in notes
    )

    # offset보다 이전에도 grid가 존재할 수 있으므로
    # 0초 이전까지 역산해서 시작점을 맞춘다.
    time = offset

    while time - grid_seconds >= 0:
        time -= grid_seconds

    grid = []

    while time <= end_time + grid_seconds:
        if time >= 0:
            grid.append(
                float(time)
            )

        time += grid_seconds

    return grid


def analyze_rhythm(
    notes,
    min_bpm=60,
    max_bpm=180,
    subdivision=2
):
    """
    허밍 멜로디 노트로부터
    BPM 후보와 리듬 grid를 분석한다.
    """

    candidates = estimate_bpm_candidates(
        notes,
        min_bpm=min_bpm,
        max_bpm=max_bpm,
    )

    ranked = cluster_bpm_candidates(
        candidates
    )

    if not ranked:
        return None

    best_bpm = ranked[0]["bpm"]

    offset = find_best_grid_offset(
        notes,
        best_bpm,
        subdivision=subdivision,
    )

    grid = create_grid(
        notes,
        best_bpm,
        offset,
        subdivision=subdivision,
    )

    return {
        "bpm": best_bpm,
        "offset": offset,
        "subdivision": subdivision,
        "grid": grid,
        "candidates": ranked[:5],
    }