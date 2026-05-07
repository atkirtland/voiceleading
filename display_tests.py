import unittest
import mido
from display import export_microtonal_midi, BEND_SEMITONES, OUTPUT_DIR


class TestMicrotonalMidi(unittest.TestCase):

    def test_31edo_chromatic_scale_has_nonzero_pitchbend(self):
        """
        Verify that the microtonal MIDI output works correctly using pitch bends by writing a 31-tone chromatic scale in 31-EDO from C4 to C5. The correctness can be verified by ear.
        """
        # 124 = C4 in 31-EDO (4 octaves * 31 steps/octave)
        c4 = 124
        # C4 to C5 inclusive
        sequence = [[c4 + step] * 4 for step in range(32)]
        export_microtonal_midi(sequence, output_name="test_31edo_chromatic", edo=31)

        midi_path = OUTPUT_DIR / "test_31edo_chromatic_microtonal.mid"
        mid = mido.MidiFile(str(midi_path))

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

        # We verify the correctness of the calculated pitch bends by ensuring there are exactly 30*4=120 nonzero bends. Because 12 and 31 are coprime, the bends align to be 0 only at the octave boundaries. So despite there being (31+1)*4=128 total tones, 120 of them have nonzero bends.
        nonzero_bends = [b for b in all_bends if b != 0]
        self.assertEqual(
            len(nonzero_bends), 30 * 4,
            f"Expected {30 * 4} non-zero pitchwheel messages (30 microtonal steps × 4 voices), "
            f"got {len(nonzero_bends)}"
        )


if __name__ == "__main__":
    unittest.main()
