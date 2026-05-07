import unittest
from main import generate_efficient_voice_leading, get_valid_midi_notes
from chords import build_universal_scale, build_chords

NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

EXPECTED_BASS = [50, 45, 47, 42, 43, 38, 43, 45]

class TestPachelbelBassLine(unittest.TestCase):
    """Tests that the bass line found by the Pachelbel's canon example does have the right pitches, the ones specified in `EXPECTED_BASS` above."""

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


class TestCircleOfFifthsStructure(unittest.TestCase):
    """Ensures that the synthesized I-IV-VII-III-VI-II-V-I voice leading for the C major scale correctly has that the root of each chord is a fifth after the previous chord root. I.e. they form a Circle of Fifths."""

    def test_roots_descend_by_diatonic_fifth(self):
        diatonic_cmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 0}
        scale_cmaj = build_universal_scale(**diatonic_cmaj)
        chords_cmaj = build_chords(scale_cmaj["Pitches"], edo=12, chord_size=3, tonic=0)
        diatonic_cmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_cmaj)}
        circle_progression = ["I", "IV", "VII", "III", "VI", "II", "V", "I"]
        circle_pcs = [diatonic_cmaj_chords[numeral] for numeral in circle_progression]

        # ordered list of pitch classes in the scale
        scale_pcs = scale_cmaj["Pitches"]
        n = len(scale_pcs)

        for i in range(len(circle_pcs) - 1):
            prev_root = circle_pcs[i][0]
            curr_root = circle_pcs[i + 1][0]
            prev_idx = scale_pcs.index(prev_root)
            curr_idx = scale_pcs.index(curr_root)

            # a fifth is 4 scale steps
            descent_in_degrees = (prev_idx - curr_idx) % n
            self.assertEqual(
                descent_in_degrees, 4,
                f"Step {i}→{i+1}: root {prev_root}→{curr_root} is not a descending diatonic fifth"
            )


if __name__ == "__main__":
    unittest.main()
