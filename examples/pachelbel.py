"""
Synthesizing something resembling very loosely Pachelbel's canon. Uses D major chords, and gets the bass line right. Notice that the `pachelbel_constraints` function shows that the bass line is just the root of each chord in the given progression; we don't have to manually specify the bass line, just the chord progression.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z3 import Or
from main import generate_efficient_voice_leading, get_valid_midi_notes, NUMERALS
from chords import build_universal_scale, build_chords
from display import export_to_music21, export_scala_file

diatonic_dmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 2}
scale_dmaj = build_universal_scale(**diatonic_dmaj)
chords_dmaj = build_chords(scale_dmaj["Pitches"], edo=12, chord_size=3, tonic=2)
diatonic_dmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_dmaj)}

pachelbel_progression = ["I", "V", "VI", "III", "IV", "I", "IV", "V"]
pachelbel_pcs = [diatonic_dmaj_chords[numeral] for numeral in pachelbel_progression]

Dmaj = [50, 57, 62, 66]
pachelbel_ranges = {
    0: (38, 53),
    1: (50, 66),
    2: (54, 73),
    3: (62, 81),
}

def pachelbel_constraints(opt, voices):
    for t, chord_pcs in enumerate(pachelbel_pcs):
        root_pc = chord_pcs[0]
        bass_min, bass_max = pachelbel_ranges[0]
        bass_candidates = get_valid_midi_notes(root_pc, bass_min, bass_max)
        opt.add(Or([voices[t][0] == note for note in bass_candidates]))

sequence_data = generate_efficient_voice_leading(Dmaj, pachelbel_pcs, metric="L1", ranges=pachelbel_ranges, optimize=True, extra_constraints=pachelbel_constraints, edo=12)
export_to_music21(sequence_data, output_name="pachelbel", save_midi=True, display=False, edo=12)
# export_scala_file(12, "12_EDO")
