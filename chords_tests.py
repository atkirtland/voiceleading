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

if __name__ == "__main__":
    unittest.main()