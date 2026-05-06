import unittest
from main import generate_efficient_voice_leading, get_valid_midi_notes
from chords import build_universal_scale, build_chords

NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

EXPECTED_BASS = [50, 45, 47, 42, 43, 38, 43, 45]


class TestPachelbelBassLine(unittest.TestCase):

    def test_bass_line(self):
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
            from z3 import Or
            for t, chord_pcs in enumerate(pachelbel_pcs):
                root_pc = chord_pcs[0]
                bass_min, bass_max = pachelbel_ranges[0]
                bass_candidates = get_valid_midi_notes(root_pc, bass_min, bass_max)
                opt.add(Or([voices[t][0] == note for note in bass_candidates]))

        result = generate_efficient_voice_leading(
            Dmaj, pachelbel_pcs, metric="L1",
            ranges=pachelbel_ranges, optimize=True,
            extra_constraints=pachelbel_constraints, edo=12
        )

        bass_line = [chord[0] for chord in result]
        self.assertEqual(bass_line, EXPECTED_BASS)


if __name__ == "__main__":
    unittest.main()
