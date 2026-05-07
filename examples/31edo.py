"""
Synthesizes a chord progression in the 31-EDO tuning system.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import generate_efficient_voice_leading, NUMERALS
from chords import build_universal_scale, build_chords
from display import export_to_music21, export_scala_file

diatonic_31 = {"edo": 31, "generators": [18], "dimensions": [7], "chain_starts": [-1], "tonic": 0}
scale_31 = build_universal_scale(**diatonic_31)
chords_31 = build_chords(scale_31["Pitches"], edo=31, chord_size=3, tonic=0)
diatonic_31_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_31)}
print("31-EDO scale pitches:", scale_31["Pitches"])
print("31-EDO chord pcs — I:", diatonic_31_chords["I"],
      " IV:", diatonic_31_chords["IV"],
      " V:", diatonic_31_chords["V"],
      " VI:", diatonic_31_chords["VI"])

progression_31 = ["I", "VI", "IV", "V", "I"]
pcs_31 = [diatonic_31_chords[numeral] for numeral in progression_31]

C_31 = [93, 111, 124, 134]
ranges_31 = {
    0: (62, 99),
    1: (93, 124),
    2: (111, 142),
    3: (124, 155),
}

sequence_data_31 = generate_efficient_voice_leading(C_31, pcs_31, metric="L1", ranges=ranges_31, optimize=True, edo=31)
export_to_music21(sequence_data_31, output_name="31edo_diatonic", save_midi=True, display=False, edo=31)
# export_scala_file(31, "31_EDO")
