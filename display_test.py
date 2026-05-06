import unittest
import mido
from display import export_microtonal_midi, BEND_SEMITONES, OUTPUT_DIR


class TestMicrotonalMidi(unittest.TestCase):

    def test_31edo_chromatic_scale_has_nonzero_pitchbend(self):
        """
        Walk all 31 steps from C4 to C5 in 31-EDO (a full chromatic octave),
        with all four voices in unison so the gradual pitch climb is clearly
        audible when played back.

        19 of the 31 steps land between 12-EDO semitones, so the pitchwheel
        messages for those steps must be non-zero to tune them correctly.
        """
        # 124 = C4 in 31-EDO (4 octaves * 31 steps/octave)
        c4 = 124
        sequence = [[c4 + step] * 4 for step in range(32)]  # C4 up to C5 inclusive
        export_microtonal_midi(sequence, output_name="test_31edo_chromatic", edo=31)

        midi_path = OUTPUT_DIR / "test_31edo_chromatic_microtonal.mid"
        mid = mido.MidiFile(str(midi_path))

        # Collect all pitchwheel values across all voice tracks
        all_bends = [
            msg.pitch
            for track in mid.tracks
            for msg in track
            if msg.type == 'pitchwheel'
        ]

        self.assertTrue(len(all_bends) > 0, "No pitchwheel messages found in MIDI file")
        self.assertTrue(
            any(bend != 0 for bend in all_bends),
            f"All pitchwheel values are zero — microtonal offsets are not being encoded. "
            f"Bends found: {all_bends}"
        )

        # Verify the exact count of non-zero bends.
        # 31-EDO and 12-EDO share a common pitch only at the octave boundaries
        # (steps 0 and 31 = C4 and C5). All 30 steps in between are microtonal,
        # so across 4 voices that's 30 * 4 = 120 non-zero bend messages.
        nonzero_bends = [b for b in all_bends if b != 0]
        self.assertEqual(
            len(nonzero_bends), 30 * 4,
            f"Expected {30 * 4} non-zero pitchwheel messages (30 microtonal steps × 4 voices), "
            f"got {len(nonzero_bends)}"
        )


if __name__ == "__main__":
    unittest.main()
