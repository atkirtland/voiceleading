import unittest
from main import generate_efficient_voice_leading, get_valid_midi_notes
from chords import build_scale, build_chords

NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

EXPECTED_BASS = [50, 45, 47, 42, 43, 38, 43, 45]

class TestPachelbelBassLine(unittest.TestCase):
    """Tests that the bass line found by the Pachelbel's canon example does have the right pitches, the ones specified in `EXPECTED_BASS` above."""

    def test_bass_line(self):
        diatonic_dmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 2}
        scale_dmaj = build_scale(**diatonic_dmaj)
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
        scale_cmaj = build_scale(**diatonic_cmaj)
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


class TestGenerateEfficientVoiceLeading(unittest.TestCase):

    def setUp(self):
        diatonic_cmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 0}
        scale_cmaj = build_scale(**diatonic_cmaj)
        chords_cmaj = build_chords(scale_cmaj["Pitches"], edo=12, chord_size=3, tonic=0)
        diatonic_cmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_cmaj)}

        self.edo = 12
        self.start_chord = [48, 55, 60, 64]  # C3 G3 C4 E4
        self.ranges = {
            0: (36, 53),
            1: (48, 65),
            2: (53, 72),
            3: (60, 84),
        }
        self.two_chord_pcs = [
            diatonic_cmaj_chords["I"],
            diatonic_cmaj_chords["V"],
        ]
        self.four_chord_pcs = [
            diatonic_cmaj_chords["I"],
            diatonic_cmaj_chords["IV"],
            diatonic_cmaj_chords["V"],
            diatonic_cmaj_chords["I"],
        ]

    def _run(self, progression_pcs=None, **kwargs):
        if progression_pcs is None:
            progression_pcs = self.two_chord_pcs
        defaults = dict(metric="L1", ranges=self.ranges, optimize=True, edo=self.edo)
        defaults.update(kwargs)
        return generate_efficient_voice_leading(self.start_chord, progression_pcs, **defaults)

    def test_output_length_matches_progression(self):
        """The number of timesteps is the same in the voice leading and the input chord progression"""
        result = self._run()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), len(self.two_chord_pcs))

    def test_each_chord_has_correct_number_of_voices(self):
        """The number of voices is correct"""
        result = self._run()
        self.assertIsNotNone(result)
        num_voices = len(self.start_chord)
        for t, chord in enumerate(result):
            self.assertEqual(len(chord), num_voices, f"Wrong voice count at step {t}")

    def test_first_chord_equals_start_chord(self):
        """first chord in the voice leading equals the provided initial chord"""
        result = self._run()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.start_chord)

    def test_all_voices_within_ranges(self):
        """all notes remain in the provided ranges"""
        result = self._run()
        self.assertIsNotNone(result)
        for t, chord in enumerate(result):
            for v, note in enumerate(chord):
                lo, hi = self.ranges[v]
                self.assertGreaterEqual(note, lo, f"Step {t} voice {v}: {note} below min {lo}")
                self.assertLessEqual(note, hi, f"Step {t} voice {v}: {note} above max {hi}")

    def test_each_voice_matches_pitch_class(self):
        """each note is an an allowed pitch class"""
        result = self._run()
        self.assertIsNotNone(result)
        for t, chord in enumerate(result):
            allowed_pcs = set(self.two_chord_pcs[t])
            for v, note in enumerate(chord):
                self.assertIn(
                    note % self.edo, allowed_pcs,
                    f"Step {t} voice {v}: note {note} (pc {note % self.edo}) not in {allowed_pcs}"
                )

    def test_all_pitch_classes_covered(self):
        """at each time step, all pitch classes do have a note"""
        result = self._run()
        self.assertIsNotNone(result)
        for t, chord in enumerate(result):
            present_pcs = {note % self.edo for note in chord}
            for pc in self.two_chord_pcs[t]:
                self.assertIn(pc, present_pcs, f"Step {t}: pitch class {pc} not covered")

    def test_no_voice_crossing(self):
        """voices do not cross"""
        result = self._run()
        self.assertIsNotNone(result)
        for t, chord in enumerate(result):
            for v in range(len(chord) - 1):
                self.assertLess(
                    chord[v], chord[v + 1],
                    f"Step {t}: voice crossing between voice {v} ({chord[v]}) and {v+1} ({chord[v+1]})"
                )

    def test_longer_progression_output_shape(self):
        """output shape is correct"""
        result = self._run(progression_pcs=self.four_chord_pcs)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        for t, chord in enumerate(result):
            self.assertEqual(len(chord), len(self.start_chord))

    def test_unsat_returns_none(self):
        """gets unsat when it should; start chord has 48 for the initial voice, but the range forces it to be 37"""
        impossible_ranges = {
            0: (37, 37),
            1: (48, 65),
            2: (53, 72),
            3: (60, 84),
        }
        result = generate_efficient_voice_leading(
            self.start_chord, self.two_chord_pcs,
            metric="L1", ranges=impossible_ranges, optimize=True, edo=self.edo
        )
        self.assertIsNone(result)

    def test_optimize_false_also_valid(self):
        """optimize false also return something reasonable"""
        result = self._run(optimize=False)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), len(self.two_chord_pcs))
        self.assertEqual(result[0], self.start_chord)
        allowed_pcs = set(self.two_chord_pcs[1])
        for v, note in enumerate(result[1]):
            self.assertIn(note % self.edo, allowed_pcs)

    def test_single_chord_progression(self):
        """Progression of a single timestep, so it just returns the start chord"""
        result = self._run(progression_pcs=self.two_chord_pcs[:1])
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.start_chord)

    def test_l1_total_distance_is_non_negative(self):
        """L1 distance is not negative"""
        result = self._run(metric="L1")
        self.assertIsNotNone(result)
        total = sum(
            abs(result[t + 1][v] - result[t][v])
            for t in range(len(result) - 1)
            for v in range(len(self.start_chord))
        )
        self.assertGreaterEqual(total, 0)


class TestGetValidMidiNotes(unittest.TestCase):

    def test_basic_correctness(self):
        """Pitch class 0 in range [36, 84] with 12-EDO should return exactly C in five octaves."""
        result = get_valid_midi_notes(0, 36, 84)
        self.assertEqual(result, [36, 48, 60, 72, 84])

    def test_empty_range(self):
        """There are no notes in pitch class 0 (C) in the specified range"""
        result = get_valid_midi_notes(0, 37, 47)
        self.assertEqual(result, [])

    def test_boundary_inclusion(self):
        """Boundaries are included properly"""
        result = get_valid_midi_notes(0, 36, 36)
        self.assertEqual(result, [36])

    def test_non_matching_boundary(self):
        """But boundaries are only included when they should be"""
        result = get_valid_midi_notes(1, 36, 36)
        self.assertEqual(result, [])

    def test_ascending_order(self):
        """Results are sorted"""
        result = get_valid_midi_notes(2, 36, 84)
        self.assertEqual(result, sorted(result))

    def test_all_results_match_pitch_class(self):
        """All found notes are actually in the right pitch class"""
        pitch_class = 5
        result = get_valid_midi_notes(pitch_class, 20, 100)
        for note in result:
            self.assertEqual(note % 12, pitch_class)

    def test_non_12_edo(self):
        """31-EDO basic test"""
        result = get_valid_midi_notes(0, 0, 62, edo=31)
        self.assertEqual(result, [0, 31, 62])

    def test_non_12_edo_pitch_class_invariant(self):
        """Same as test_all_results_match_pitch_class but with 19-EDO"""
        edo = 19
        pitch_class = 7
        result = get_valid_midi_notes(pitch_class, 0, 200, edo=edo)
        for note in result:
            self.assertEqual(note % edo, pitch_class)


if __name__ == "__main__":
    unittest.main()
