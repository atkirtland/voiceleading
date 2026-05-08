"""
A basic C major chord progression.
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

cmaj_progression = ["I", "VI", "IV", "V", "I"]
cmaj_pcs = [diatonic_cmaj_chords[numeral] for numeral in cmaj_progression]

Cmaj = [48, 55, 60, 64]
voice_ranges = {
    0: (36, 53),
    1: (48, 65),
    2: (53, 72),
    3: (60, 84),
}

sequence_data = generate_efficient_voice_leading(Cmaj, cmaj_pcs, metric="L1", ranges=voice_ranges, optimize=True, edo=12)
export_to_music21(sequence_data, output_name="cmaj", save_midi=True, display=False)
# export_scala_file(12, "12_EDO")
