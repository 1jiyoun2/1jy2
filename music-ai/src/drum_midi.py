from pathlib import Path
import numpy as np

import librosa
import mido
from mido import Message, MidiFile, MidiTrack


DRUM_NOTES = {
    "kick": 36,
    "snare": 38,
    "hh": 42,
    "hihat": 42,
    "toms": 45,
    "crash": 49,
    "ride": 51,
}


DETECTION_SETTINGS = {
    "kick":  {"delta": 0.20, "wait": 12},
    "snare": {"delta": 0.18, "wait": 10},
    "hh":    {"delta": 0.10, "wait": 4},
    "hihat": {"delta": 0.10, "wait": 4},
    "toms":  {"delta": 0.22, "wait": 12},
    "ride":  {"delta": 0.15, "wait": 8},
    "crash": {"delta": 0.20, "wait": 12},
}


def detect_hits(audio_path, instrument):
    y, sr = librosa.load(
        audio_path,
        sr=None,
        mono=True
    )

    settings = {
        "kick":  {"delta": 0.25, "wait": 12, "percentile": 65},
        "snare": {"delta": 0.23, "wait": 10, "percentile": 65},
        "hh":    {"delta": 0.18, "wait": 5,  "percentile": 55},
        "hihat": {"delta": 0.18, "wait": 5,  "percentile": 55},
        "toms":  {"delta": 0.30, "wait": 14, "percentile": 75},
        "ride":  {"delta": 0.25, "wait": 10, "percentile": 70},
        "crash": {"delta": 0.30, "wait": 14, "percentile": 75},
    }

    config = settings.get(
        instrument,
        {"delta": 0.25, "wait": 10, "percentile": 70}
    )

    # 순간적인 타격 강도 계산
    onset_env = librosa.onset.onset_strength(
        y=y,
        sr=sr
    )

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        backtrack=False,
        delta=config["delta"],
        wait=config["wait"]
    )

    if len(onset_frames) == 0:
        return []

    # 검출된 타격들의 강도
    strengths = onset_env[onset_frames]

    # 약한 타격(bleed)을 제거하기 위한 기준값
    threshold = np.percentile(
        strengths,
        config["percentile"]
    )

    strong_frames = onset_frames[
        strengths >= threshold
    ]

    onset_times = librosa.frames_to_time(
        strong_frames,
        sr=sr
    )

    return onset_times


def create_track_events(
    instrument,
    audio_path,
    ticks_per_beat,
    tempo
):
    note = DRUM_NOTES[instrument]

    print(f"{instrument} 타격 분석 중...")

    hit_times = detect_hits(
        audio_path,
        instrument
    )

    print(f"  감지된 타격: {len(hit_times)}")

    events = []

    note_length = 30

    for hit_time in hit_times:
        tick = round(
            mido.second2tick(
                hit_time,
                ticks_per_beat,
                tempo
            )
        )

        events.append(
            (
                tick,
                1,
                Message(
                    "note_on",
                    channel=9,
                    note=note,
                    velocity=100,
                    time=0
                )
            )
        )

        events.append(
            (
                tick + note_length,
                0,
                Message(
                    "note_off",
                    channel=9,
                    note=note,
                    velocity=0,
                    time=0
                )
            )
        )

    events.sort(
        key=lambda event: (
            event[0],
            event[1]
        )
    )

    return events


def write_events_to_track(
    track,
    events
):
    previous_tick = 0

    for absolute_tick, _, message in events:
        delta = absolute_tick - previous_tick

        message.time = delta
        track.append(message)

        previous_tick = absolute_tick


def create_drum_midi(
    stem_paths,
    output_path,
    bpm
):
    ticks_per_beat = 480
    tempo = mido.bpm2tempo(bpm)

    output_path = Path(output_path)

    output_dir = output_path.parent / "midi"
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    all_events = []

    for instrument, audio_path in stem_paths.items():

        if instrument not in DRUM_NOTES:
            print(
                f"지원하지 않는 악기라 건너뜁니다: "
                f"{instrument}"
            )
            continue

        events = create_track_events(
            instrument,
            audio_path,
            ticks_per_beat,
            tempo
        )

        all_events.extend(events)

        # -------------------------
        # 개별 MIDI 파일 생성
        # -------------------------

        midi = MidiFile(
            ticks_per_beat=ticks_per_beat
        )

        track = MidiTrack()
        midi.tracks.append(track)

        track.append(
            mido.MetaMessage(
                "track_name",
                name=instrument,
                time=0
            )
        )

        track.append(
            mido.MetaMessage(
                "set_tempo",
                tempo=tempo,
                time=0
            )
        )

        write_events_to_track(
            track,
            events
        )

        individual_path = (
            output_dir / f"{instrument}.mid"
        )

        midi.save(individual_path)

        print(
            f"  MIDI 저장: {individual_path}"
        )

    # -------------------------
    # 합본 MIDI 생성
    # -------------------------

    all_events.sort(
        key=lambda event: (
            event[0],
            event[1]
        )
    )

    midi_all = MidiFile(
        ticks_per_beat=ticks_per_beat
    )

    track_all = MidiTrack()
    midi_all.tracks.append(track_all)

    track_all.append(
        mido.MetaMessage(
            "track_name",
            name="drums_all",
            time=0
        )
    )

    track_all.append(
        mido.MetaMessage(
            "set_tempo",
            tempo=tempo,
            time=0
        )
    )

    write_events_to_track(
        track_all,
        all_events
    )

    all_path = (
        output_dir / "drums_all.mid"
    )

    midi_all.save(all_path)

    print(
        f"\n합본 MIDI 저장: {all_path}"
    )