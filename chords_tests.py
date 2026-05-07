import unittest
from chords import build_universal_scale, build_chords

class TestChords(unittest.TestCase):

    def test_12edo_diatonic_chords(self):
        """
        Tests that building C major produces the right pitches and chords.
        """
        scale = build_universal_scale(
            edo=12,
            generators=[7],
            dimensions=[7],
            chain_starts=[-1],
        )

        self.assertEqual(
            scale["Pitches"], 
            [0, 2, 4, 5, 7, 9, 11], 
            f"Unexpected diatonic pitches: {scale['Pitches']}"
        )

        chords = build_chords(scale["Pitches"], edo=12, chord_size=3)
        chords_mod12 = [[p % 12 for p in chord] for chord in chords]

        expected = [
            [0, 4, 7],   # I   – C major
            [2, 5, 9],   # ii  – D minor
            [4, 7, 11],  # iii – E minor
            [5, 9, 0],   # IV  – F major
            [7, 11, 2],  # V   – G major
            [9, 0, 4],   # vi  – A minor
            [11, 2, 5],  # vii°– B dim
        ]

        self.assertEqual(
            chords_mod12, 
            expected, 
            f"Chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
        )

    def test_12edo_diatonic_seventh_chords(self):
        """
        As above, but for seventh chords.
        """
        scale = build_universal_scale(
            edo=12,
            generators=[7],
            dimensions=[7],
            chain_starts=[-1],
        )

        chords = build_chords(scale["Pitches"], edo=12, chord_size=4)
        chords_mod12 = [[p % 12 for p in chord] for chord in chords]

        expected = [
            [0, 4, 7, 11],   # Imaj7  – C major 7th
            [2, 5, 9, 0],    # ii7    – D minor 7th
            [4, 7, 11, 2],   # iii7   – E minor 7th
            [5, 9, 0, 4],    # IVmaj7 – F major 7th
            [7, 11, 2, 5],   # V7     – G dominant 7th
            [9, 0, 4, 7],    # vi7    – A minor 7th
            [11, 2, 5, 9],   # viiø7  – B half-diminished 7th
        ]

        self.assertEqual(
            chords_mod12, 
            expected, 
            f"Seventh chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
        )

        v7_main = [p % 12 for p in [7, 11, 14, 17]]
        self.assertEqual(
            chords_mod12[4], 
            v7_main, 
            f"V7 mismatch.\n  Got:      {chords_mod12[4]}\n  Expected: {v7_main}"
        )

    def test_12edo_diatonic_step_sizes(self):
        """
        Verify that the steps and step sizes in 12-EDO diatonic scales are correct (are 1 and 2).
        """
        scale = build_universal_scale(
            edo=12,
            generators=[7],
            dimensions=[7],
            chain_starts=[-1],
        )

        self.assertCountEqual(
            scale["Steps"], 
            [2, 2, 1, 2, 2, 2, 1], 
            f"Unexpected step sequence: {scale['Steps']}"
        )
        
        self.assertEqual(
            scale["Step_Sizes"], 
            [2, 1], 
            f"Unexpected step sizes: {scale['Step_Sizes']}"
        )

    def test_12edo_pentatonic_chords(self):
        """
        Similar tests as above, but for pentatonic scales/chords.
        """
        scale = build_universal_scale(
            edo=12,
            generators=[7],
            dimensions=[5],
            chain_starts=[0],
        )

        self.assertEqual(
            scale["Pitches"], 
            [0, 2, 4, 7, 9], 
            f"Unexpected pentatonic pitches: {scale['Pitches']}"
        )
        
        self.assertCountEqual(
            scale["Steps"], 
            [2, 2, 3, 2, 3], 
            f"Unexpected step sequence: {scale['Steps']}"
        )
        
        self.assertEqual(
            scale["Step_Sizes"], 
            [3, 2], 
            f"Unexpected step sizes: {scale['Step_Sizes']}"
        )

        chords = build_chords(scale["Pitches"], edo=12, chord_size=3)
        chords_mod12 = [[p % 12 for p in chord] for chord in chords]

        expected = [
            [0, 4, 9],   # I   – C E A
            [2, 7, 0],   # II  – D G C
            [4, 9, 2],   # III – E A D
            [7, 0, 4],   # IV  – G C E
            [9, 2, 7],   # V   – A D G
        ]

        self.assertEqual(
            chords_mod12, 
            expected, 
            f"Pentatonic chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
        )

class TestBuildUniversalScaleInvariants(unittest.TestCase):

    def _make_scale(self, **kwargs):
        return build_universal_scale(**kwargs)

    def test_steps_sum_to_edo(self):
        """Across several choices of scales, the sum of the steps in the scale equals the EDO (ensures the scale loops around)"""
        for params in [
            {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 12, "generators": [7], "dimensions": [5], "chain_starts": [0]},
            {"edo": 19, "generators": [11], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 31, "generators": [18], "dimensions": [7], "chain_starts": [-1]},
        ]:
            with self.subTest(params=params):
                scale = self._make_scale(**params)
                self.assertEqual(
                    sum(scale["Steps"]), scale["EDO"],
                    f"Steps {scale['Steps']} do not sum to EDO {scale['EDO']}"
                )

    def test_pitches_sorted_and_unique(self):
        """Scale pitches are strictly increasing and unique."""
        for params in [
            {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 12, "generators": [7], "dimensions": [5], "chain_starts": [0]},
            {"edo": 31, "generators": [18], "dimensions": [7], "chain_starts": [-1]},
        ]:
            with self.subTest(params=params):
                scale = self._make_scale(**params)
                pitches = scale["Pitches"]
                self.assertEqual(pitches, sorted(set(pitches)),
                                 f"Pitches not sorted/unique: {pitches}")

    def test_pitches_in_valid_range(self):
        """All scale pitches are in [0,EDO)"""
        for params in [
            {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 19, "generators": [11], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 31, "generators": [18], "dimensions": [7], "chain_starts": [-1]},
        ]:
            with self.subTest(params=params):
                scale = self._make_scale(**params)
                edo = scale["EDO"]
                for p in scale["Pitches"]:
                    self.assertGreaterEqual(p, 0)
                    self.assertLess(p, edo)

    def test_step_sizes_unique_and_descending(self):
        """The step sizes are unique and listed largest to smallest (just a convention)."""
        for params in [
            {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1]},
            {"edo": 12, "generators": [7], "dimensions": [5], "chain_starts": [0]},
        ]:
            with self.subTest(params=params):
                scale = self._make_scale(**params)
                sizes = scale["Step_Sizes"]
                self.assertEqual(len(sizes), len(set(sizes)), "Step_Sizes has duplicates")
                self.assertEqual(sizes, sorted(sizes, reverse=True),
                                 "Step_Sizes is not sorted descending")

    def test_step_sizes_are_subset_of_steps(self):
        """Each of the found step sizes are in the list of steps."""
        scale = self._make_scale(
            edo=12, generators=[7], dimensions=[7], chain_starts=[-1]
        )
        steps_set = set(scale["Steps"])
        for size in scale["Step_Sizes"]:
            self.assertIn(size, steps_set)

    def test_tonic_transposition(self):
        """Adding 2 to the tonic actually causes all the found pitches to be shifted up by 2."""
        base = build_universal_scale(edo=12, generators=[7], dimensions=[7], chain_starts=[-1], tonic=0)
        transposed = build_universal_scale(edo=12, generators=[7], dimensions=[7], chain_starts=[-1], tonic=2)
        expected = sorted([(p + 2) % 12 for p in base["Pitches"]])
        self.assertEqual(transposed["Pitches"], expected)


class TestBuildChordsInvariants(unittest.TestCase):

    def setUp(self):
        """C major"""
        scale = build_universal_scale(
            edo=12, generators=[7], dimensions=[7], chain_starts=[-1]
        )
        self.scale_pitches = scale["Pitches"]

    def test_number_of_chords_equals_scale_length(self):
        """Get one scale degree chord for each note in the scale"""
        chords = build_chords(self.scale_pitches, edo=12, chord_size=3)
        self.assertEqual(len(chords), len(self.scale_pitches))

    def test_each_chord_has_correct_size(self):
        """the number of notes in each chord is the specified amount"""
        for chord_size in [3, 4]:
            with self.subTest(chord_size=chord_size):
                chords = build_chords(self.scale_pitches, edo=12, chord_size=chord_size)
                for i, chord in enumerate(chords):
                    self.assertEqual(len(chord), chord_size,
                                     f"Chord {i} has wrong size: {chord}")

    def test_chord_tones_drawn_from_scale(self):
        """All notes in all chords are actually in the scale"""
        chords = build_chords(self.scale_pitches, edo=12, chord_size=3)
        scale_set = set(self.scale_pitches)
        for i, chord in enumerate(chords):
            for tone in chord:
                self.assertIn(tone, scale_set,
                              f"Chord {i} contains {tone} not in scale {self.scale_pitches}")

    def test_first_chord_root_is_tonic(self):
        """The first note of the first chord is the tonic."""
        tonic = 0
        chords = build_chords(self.scale_pitches, edo=12, chord_size=3, tonic=tonic)
        self.assertEqual(chords[0][0], tonic)

    def test_tonic_not_in_scale_falls_back_to_index_zero(self):
        """When the tonic is not specified, the first note of the first chord is the lowest of the scale pitches."""
        chords = build_chords(self.scale_pitches, edo=12, chord_size=3, tonic=1)
        self.assertEqual(chords[0][0], self.scale_pitches[0])


if __name__ == "__main__":
    unittest.main()