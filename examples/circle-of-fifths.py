"""
Synthesizes chords following the C major circle of fifths.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import generate_efficient_voice_leading, NUMERALS
from chords import build_scale, build_chords
from display import export_to_music21, export_scala_file

diatonic_cmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 0}
scale_cmaj = build_scale(**diatonic_cmaj)
chords_cmaj = build_chords(scale_cmaj["Pitches"], edo=12, chord_size=3, tonic=0)
diatonic_cmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_cmaj)}

circle_progression = ["I", "IV", "VII", "III", "VI", "II", "V", "I"]
circle_pcs = [diatonic_cmaj_chords[numeral] for numeral in circle_progression]

Cmaj = [48, 55, 60, 64]
circle_ranges = {
    0: (36, 53),
    1: (48, 65),
    2: (53, 72),
    3: (60, 84),
}

sequence_data = generate_efficient_voice_leading(Cmaj, circle_pcs, metric="L1", ranges=circle_ranges, optimize=True, edo=12)
export_to_music21(sequence_data, output_name="circle_of_fifths", save_midi=True, display=False, edo=12)
# export_scala_file(12, "12_EDO")
