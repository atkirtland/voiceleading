from pathlib import Path
import music21 as m21

def export_to_music21(sequence, output_name="voice_leading"):
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
    
    # Map the Z3 integers to music21 Note objects
    for chord_voicing in sequence:
        for i, midi_pitch in enumerate(chord_voicing):
            n = m21.note.Note()
            n.pitch.midi = midi_pitch
            n.quarterLength = 1.0  # Assigns each chord a duration of 1 beat (quarter note)
            parts[i].append(n)
            
    # Stack the parts into the master score
    for p in reversed(parts):
        score.insert(0, p)
    
    #
    # Output
    #
        
    midi_path = f"{output_name}.mid"
    score.write('midi', fp=midi_path)
    print(f"MIDI saved to: {midi_path}")
    
    print("Opening sheet music visualization...")
    score.show()