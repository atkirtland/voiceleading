"""
This is the code that generates the MIDI and musicxml files.
"""
from pathlib import Path
import music21 as m21
import mido

OUTPUT_DIR = Path(__file__).parent / "output"

# MIDI pitch-bend range: ±8192 units = ±2 semitones (200 cents) by default.
# Most synths use ±2 semitones as the default bend range; we set it explicitly
# via RPN 0 (Pitch Bend Sensitivity) at the start of each track.
BEND_SEMITONES = 2
BEND_MAX = 8191

def _cents_to_pitchbend(cents_offset: float) -> int:
    """
    Convert a microtonal offset in cents to a MIDI pitch-bend integer.
    Assumes the synth's pitch-bend range has been set to ±BEND_SEMITONES semitones.
    Result is clamped to [-8192, 8191].
    """
    bend = round(cents_offset / (BEND_SEMITONES * 100) * BEND_MAX)
    return max(-8192, min(BEND_MAX, bend))

def _set_pitch_bend_range(track, channel, semitones=BEND_SEMITONES):
    """Emit the standard RPN sequence that sets pitch-bend sensitivity."""
    # RPN MSB = 0, LSB = 0 selects "Pitch Bend Sensitivity"
    track.append(mido.Message('control_change', channel=channel, control=101, value=0, time=0))
    track.append(mido.Message('control_change', channel=channel, control=100, value=0, time=0))
    track.append(mido.Message('control_change', channel=channel, control=6,   value=semitones, time=0))
    track.append(mido.Message('control_change', channel=channel, control=38,  value=0, time=0))
    # Deselect RPN so accidental data-entry messages don't change it later
    track.append(mido.Message('control_change', channel=channel, control=101, value=127, time=0))
    track.append(mido.Message('control_change', channel=channel, control=100, value=127, time=0))

def export_microtonal_midi(sequence, output_name="voice_leading", edo=12,
                           tempo_bpm=72, ticks_per_beat=480):
    """
    Write a multichannel pitch-bend MIDI file so that microtonal tunings are
    audible in any standard softsynth.

    Each of the 4 voices gets its own MIDI channel (1–4) and its own track.
    Before every note-on the correct pitch-bend is sent on that channel, so
    simultaneous voices never interfere with each other's tuning.

    EDO step → frequency mapping:
        total_cents = step * (1200 / edo)
        midi_note   = round(total_cents / 100)        ← nearest 12-EDO semitone
        bend_cents  = total_cents - midi_note * 100   ← residual, in (−50, +50]
    """
    cents_per_step = 1200.0 / edo
    ticks_per_note = ticks_per_beat  # one quarter-note per chord slot
    velocity = 80
    tempo_us = mido.bpm2tempo(tempo_bpm)

    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    # Tempo track (track 0)
    tempo_track = mido.MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=tempo_us, time=0))
    tempo_track.append(mido.MetaMessage('end_of_track', time=0))

    voice_names = ['Bass', 'Tenor', 'Alto', 'Soprano']
    # Channels 0-indexed internally; avoid channel 9 (drums)
    channels = [0, 1, 2, 3]

    for voice_idx, (name, channel) in enumerate(zip(voice_names, channels)):
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage('track_name', name=name, time=0))
        # Grand piano on every voice
        track.append(mido.Message('program_change', channel=channel, program=0, time=0))
        _set_pitch_bend_range(track, channel)

        for chord_voicing in sequence:
            step = chord_voicing[voice_idx]
            total_cents = step * cents_per_step
            midi_note = round(total_cents / 100)
            bend_cents = total_cents - midi_note * 100
            bend_value = _cents_to_pitchbend(bend_cents)

            # Pitch-bend must arrive before the note-on (time=0 = same tick)
            track.append(mido.Message('pitchwheel', channel=channel,
                                      pitch=bend_value, time=0))
            track.append(mido.Message('note_on', channel=channel,
                                      note=midi_note, velocity=velocity, time=0))
            # note_off after one beat
            track.append(mido.Message('note_off', channel=channel,
                                      note=midi_note, velocity=0, time=ticks_per_note))

        track.append(mido.MetaMessage('end_of_track', time=0))

    OUTPUT_DIR.mkdir(exist_ok=True)
    midi_path = OUTPUT_DIR / f"{output_name}_microtonal.mid"
    mid.save(str(midi_path))
    print(f"Microtonal MIDI saved to: {midi_path}")


def export_to_music21(sequence, output_name="voice_leading", save_midi=True, display=False, edo=12):
    """
    Converts a sequence of Z3 MIDI chords into a standard SATB score and MIDI file.
    Sequence format expected: [[Bass, Tenor, Alto, Soprano], ...]

    For non-12-EDO tunings, also writes a separate multichannel pitch-bend MIDI
    (via export_microtonal_midi) so the microtonality is audible in any softsynth.
    """

    #
    # Prepare MusicXML reader
    #
    env = m21.environment.UserSettings()
    path = Path.home() / ".local/bin/MuseScore-Studio-4.6.5.253511702-x86_64.AppImage"
    env['musescoreDirectPNGPath'] = path
    env['musicxmlPath'] = path

    #
    # Prepare score
    #

    score = m21.stream.Score()
    
    parts = [
        m21.stream.Part(id='Bass'),
        m21.stream.Part(id='Tenor'),
        m21.stream.Part(id='Alto'),
        m21.stream.Part(id='Soprano')
    ]
    
    # Assign standard choral clefs for readability
    parts[0].append(m21.clef.BassClef())
    # parts[1].append(m21.clef.BassClef())   # Tenor uses Bass or Treble8ve
    parts[1].append(m21.clef.Treble8vbClef())
    parts[2].append(m21.clef.TrebleClef())
    parts[3].append(m21.clef.TrebleClef())
    
    # Map the Z3 integers to music21 Note objects.
    # For non-12-EDO tunings the voice values are EDO steps, not raw MIDI numbers.
    # We convert via cents: step * (1200 / edo) cents above MIDI 0, then split into
    # an integer MIDI semitone plus a microtonal adjustment in cents.
    cents_per_step = 1200.0 / edo
    for chord_voicing in sequence:
        for i, step in enumerate(chord_voicing):
            total_cents = step * cents_per_step
            midi_int = round(total_cents / 100)
            microtone_cents = total_cents - midi_int * 100
            n = m21.note.Note()
            n.pitch.midi = midi_int
            if abs(microtone_cents) > 0.01:
                n.pitch.microtone = m21.pitch.Microtone(microtone_cents)
            n.quarterLength = 1.0
            parts[i].append(n)
            
    # Stack the parts into the master score
    for p in reversed(parts):
        score.insert(0, p)
    
    #
    # Output
    #
    OUTPUT_DIR.mkdir(exist_ok=True)

    musicxml_path = OUTPUT_DIR / f"{output_name}.musicxml"
    score.write('musicxml', fp=str(musicxml_path))
    print(f"MusicXML saved to: {musicxml_path}")

    if save_midi:
        if edo != 12:
            # Write a proper microtonal MIDI with per-voice pitch-bend
            export_microtonal_midi(sequence, output_name=output_name, edo=edo)
        else:
            midi_path = OUTPUT_DIR / f"{output_name}.mid"
            score.write('midi', fp=str(midi_path))
            print(f"MIDI saved to: {midi_path}")
    
    if display:
        print("Opening sheet music visualization...")
        score.show()

"""
This is not currently in use- scl files can potentially support "purer" microtonal MIDI files without using pitch bends, but so far we have only used and tested the pitch bend MIDI files produced with other functions in this file.
"""
def export_scala_file(edo, filename="tuning"):
    """
    Generates a Scala (.scl) file for a given Equal Temperament system.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / f"{filename}.scl"
    cents_per_step = 1200.0 / edo
    
    with open(str(filepath), 'w') as f:
        # 1. Standard Scala header
        f.write(f"! {filename}.scl\n")
        f.write(f"! Generated from Z3 optimization\n")
        f.write(f"{edo} Equal Divisions of the Octave\n")
        f.write(f" {edo}\n")
        f.write("!\n")
        
        # 2. Write the scale degrees (Scala format omits the 0 cents starting point)
        for step in range(1, edo + 1):
            cents_value = step * cents_per_step
            # Scala requires cents to have a decimal point
            f.write(f" {cents_value:.5f}\n")
            
    print(f"Scala tuning file saved to: {filepath}")
