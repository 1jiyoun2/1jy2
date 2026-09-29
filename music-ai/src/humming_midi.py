from pathlib import Path

import mido
from mido import Message, MidiFile, MidiTrack


def create_melody_midi(
    notes,
    output_path,
    bpm=120
):
    ticks_per_beat = 480
    tempo = mido.bpm2tempo(bpm)

    midi = MidiFile(
        ticks_per_beat=ticks_per_beat
    )

    track = MidiTrack()
    midi.tracks.append(track)

    track.append(
        mido.MetaMessage(
            "track_name",
            name="Humming Melody",
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

    events = []

    for note in notes:
        start_tick = round(
            mido.second2tick(
                note["start"],
                ticks_per_beat,
                tempo
            )
        )

        end_tick = round(
            mido.second2tick(
                note["end"],
                ticks_per_beat,
                tempo
            )
        )

        midi_note = note["midi"]

        events.append(
            (
                start_tick,
                1,
                Message(
                    "note_on",
                    note=midi_note,
                    velocity=100,
                    time=0
                )
            )
        )

        events.append(
            (
                end_tick,
                0,
                Message(
                    "note_off",
                    note=midi_note,
                    velocity=0,
                    time=0
                )
            )
        )

    # 모든 이벤트를 절대시간 순서대로 정렬
    events.sort(
        key=lambda event: (
            event[0],
            event[1]
        )
    )

    previous_tick = 0

    for absolute_tick, _, message in events:
        message.time = absolute_tick - previous_tick
        track.append(message)
        previous_tick = absolute_tick

    track.append(
        mido.MetaMessage(
            "end_of_track",
            time=0
        )
    )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    midi.save(output_path)

def create_pad_midi(
    progression,
    output_path,
    bpm=120,
    base_octave=3,
    velocity=55
):
    ticks_per_beat = 480
    tempo = mido.bpm2tempo(bpm)

    midi = MidiFile(
        ticks_per_beat=ticks_per_beat
    )

    track = MidiTrack()
    midi.tracks.append(track)

    track.append(
        mido.MetaMessage(
            "track_name",
            name="Harmony Pad",
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

    events = []

    octave_base = (
        12 * (base_octave + 1)
    )

    for chord in progression:

        start_tick = round(
            mido.second2tick(
                chord["start"],
                ticks_per_beat,
                tempo
            )
        )

        end_tick = round(
            mido.second2tick(
                chord["end"],
                ticks_per_beat,
                tempo
            )
        )

        midi_notes = []

        for pitch_class in chord["notes"]:

            midi_note = (
                octave_base
                + pitch_class
            )

            midi_notes.append(
                midi_note
            )

        for midi_note in midi_notes:

            events.append(
                (
                    start_tick,
                    1,
                    Message(
                        "note_on",
                        note=midi_note,
                        velocity=velocity,
                        time=0
                    )
                )
            )

            events.append(
                (
                    end_tick,
                    0,
                    Message(
                        "note_off",
                        note=midi_note,
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

    previous_tick = 0

    for absolute_tick, _, message in events:

        message.time = (
            absolute_tick
            - previous_tick
        )

        track.append(message)

        previous_tick = absolute_tick

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    midi.save(output_path)

def create_combined_midi(
    notes,
    progression,
    output_path,
    bpm=120,
    pad_velocity=55,
):
    ticks_per_beat = 480
    tempo = mido.bpm2tempo(bpm)

    midi = MidiFile(
        ticks_per_beat=ticks_per_beat
    )

    # -------------------------
    # Melody Track
    # -------------------------

    melody_track = MidiTrack()
    midi.tracks.append(melody_track)

    melody_track.append(
        mido.MetaMessage(
            "track_name",
            name="Humming Melody",
            time=0
        )
    )

    melody_track.append(
        mido.MetaMessage(
            "set_tempo",
            tempo=tempo,
            time=0
        )
    )

    melody_events = []

    for note in notes:

        start_tick = round(
            mido.second2tick(
                note["start"],
                ticks_per_beat,
                tempo
            )
        )

        end_tick = round(
            mido.second2tick(
                note["end"],
                ticks_per_beat,
                tempo
            )
        )

        melody_events.append(
            (
                start_tick,
                1,
                Message(
                    "note_on",
                    note=note["midi"],
                    velocity=100,
                    time=0
                )
            )
        )

        melody_events.append(
            (
                end_tick,
                0,
                Message(
                    "note_off",
                    note=note["midi"],
                    velocity=0,
                    time=0
                )
            )
        )

    melody_events.sort(
        key=lambda event: (
            event[0],
            event[1]
        )
    )

    previous_tick = 0

    for absolute_tick, _, message in melody_events:

        message.time = (
            absolute_tick
            - previous_tick
        )

        melody_track.append(
            message
        )

        previous_tick = absolute_tick

    # -------------------------
    # Harmony Pad Track
    # -------------------------

    pad_track = MidiTrack()
    midi.tracks.append(pad_track)

    pad_track.append(
        mido.MetaMessage(
            "track_name",
            name="Harmony Pad",
            time=0
        )
    )

    pad_events = []

    # C3 부근부터 화음을 배치
    octave_base = 48

    for chord in progression:

        start_tick = round(
            mido.second2tick(
                chord["start"],
                ticks_per_beat,
                tempo
            )
        )

        end_tick = round(
            mido.second2tick(
                chord["end"],
                ticks_per_beat,
                tempo
            )
        )

        for pitch_class in chord["notes"]:

            midi_note = (
                octave_base
                + pitch_class
            )

            pad_events.append(
                (
                    start_tick,
                    1,
                    Message(
                        "note_on",
                        note=midi_note,
                        velocity=pad_velocity,
                        time=0
                    )
                )
            )

            pad_events.append(
                (
                    end_tick,
                    0,
                    Message(
                        "note_off",
                        note=midi_note,
                        velocity=0,
                        time=0
                    )
                )
            )

    pad_events.sort(
        key=lambda event: (
            event[0],
            event[1]
        )
    )

    previous_tick = 0

    for absolute_tick, _, message in pad_events:

        message.time = (
            absolute_tick
            - previous_tick
        )

        pad_track.append(
            message
        )

        previous_tick = absolute_tick

    # -------------------------
    # 저장
    # -------------------------

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    midi.save(
        output_path
    )