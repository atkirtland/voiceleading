from pathlib import Path
import music21 as m21

OUTPUT_DIR = Path(__file__).parent / "output"

def export_to_music21(sequence, output_name="voice_leading", save_midi=True, display=False, edo=12):
    """
    Converts a sequence of Z3 MIDI chords into a standard SATB score and MIDI file.
    Sequence format expected: [[Bass, Tenor, Alto, Soprano], ...]
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
            midi_int = int(total_cents / 100)          # nearest semitone below
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
        midi_path = OUTPUT_DIR / f"{output_name}.mid"
        score.write('midi', fp=str(midi_path))
        print(f"MIDI saved to: {midi_path}")
    
    if display:
        print("Opening sheet music visualization...")
        score.show()

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
