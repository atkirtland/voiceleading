# 12-note EDO generated is correct; there are some generators so that it works...for each of the listed scales

from chords import build_universal_scale, build_chords


def test_12edo_diatonic_chords():
    """
    Verify that build_universal_scale + build_chords produces the standard
    diatonic triads for 12-EDO, matching the harmony dictionary in main.py (mod 12).
    """
    scale = build_universal_scale(
        edo=12,
        generators=[7],
        dimensions=[7],
        chain_starts=[-1],
    )

    assert scale["Pitches"] == [0, 2, 4, 5, 7, 9, 11], (
        f"Unexpected diatonic pitches: {scale['Pitches']}"
    )

    chords = build_chords(scale["Pitches"], edo=12, chord_size=3)

    # Normalize each chord mod 12 for comparison (mirrors main.py's harmony dict mod 12)
    chords_mod12 = [[p % 12 for p in chord] for chord in chords]

    expected = [
        [0, 4, 7],   # I   – C major
        [2, 5, 9],   # ii  – D minor
        [4, 7, 11],  # iii – E minor
        [5, 9, 0],   # IV  – F major  (main.py has [5, 9, 12]; 12 % 12 == 0)
        [7, 11, 2],  # V   – G major  (main.py has [7, 11, 14]; 14 % 12 == 2)
        [9, 0, 4],   # vi  – A minor  (main.py has [9, 12, 16]; 12%12==0, 16%12==4)
        [11, 2, 5],  # vii°– B dim    (main.py has [11, 14, 17]; 14%12==2, 17%12==5)
    ]

    assert chords_mod12 == expected, (
        f"Chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
    )


def test_12edo_diatonic_seventh_chords():
    """
    Verify that build_chords with chord_size=4 produces the correct diatonic
    seventh chords for 12-EDO, with the V7 matching main.py's [7, 11, 14, 17] mod 12.
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
        [7, 11, 2, 5],   # V7     – G dominant 7th  (main.py has [7, 11, 14, 17])
        [9, 0, 4, 7],    # vi7    – A minor 7th
        [11, 2, 5, 9],   # viiø7  – B half-diminished 7th
    ]

    assert chords_mod12 == expected, (
        f"Seventh chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
    )

    # Specifically verify the V7 chord matches main.py's harmony dict (mod 12)
    v7_main = [p % 12 for p in [7, 11, 14, 17]]
    assert chords_mod12[4] == v7_main, (
        f"V7 mismatch.\n  Got:      {chords_mod12[4]}\n  Expected: {v7_main}"
    )


def test_12edo_diatonic_step_sizes():
    """
    Verify that the 12-EDO diatonic scale has the correct interval structure:
    steps are a permutation of [2, 2, 1, 2, 2, 2, 1] (W W H W W W H),
    and the only two step sizes are 2 (whole) and 1 (half).
    """
    scale = build_universal_scale(
        edo=12,
        generators=[7],
        dimensions=[7],
        chain_starts=[-1],
    )

    assert sorted(scale["Steps"]) == sorted([2, 2, 1, 2, 2, 2, 1]), (
        f"Unexpected step sequence: {scale['Steps']}"
    )
    assert scale["Step_Sizes"] == [2, 1], (
        f"Unexpected step sizes: {scale['Step_Sizes']}"
    )


def test_12edo_pentatonic_chords():
    """
    Verify that build_universal_scale + build_chords produces the correct triads
    for the 12-EDO pentatonic scale (5 consecutive fifths from 0).

    Pitches: [0, 2, 4, 7, 9]  (C D E G A)
    Steps:   a permutation of [2, 2, 3, 2, 3]  (only step sizes: 3 and 2)

    Triads (stacking every other scale degree, wrapping mod 5):
      I:   [0, 4, 9]   – C E A
      II:  [2, 7, 0]   – D G C
      III: [4, 9, 2]   – E A D
      IV:  [7, 0, 4]   – G C E
      V:   [9, 2, 7]   – A D G
    """
    scale = build_universal_scale(
        edo=12,
        generators=[7],
        dimensions=[5],
        chain_starts=[0],
    )

    assert scale["Pitches"] == [0, 2, 4, 7, 9], (
        f"Unexpected pentatonic pitches: {scale['Pitches']}"
    )
    assert sorted(scale["Steps"]) == sorted([2, 2, 3, 2, 3]), (
        f"Unexpected step sequence: {scale['Steps']}"
    )
    assert scale["Step_Sizes"] == [3, 2], (
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

    assert chords_mod12 == expected, (
        f"Pentatonic chord mismatch.\n  Got:      {chords_mod12}\n  Expected: {expected}"
    )


if __name__ == "__main__":
    test_12edo_diatonic_chords()
    test_12edo_diatonic_seventh_chords()
    test_12edo_diatonic_step_sizes()
    test_12edo_pentatonic_chords()
    print("All tests passed.")
