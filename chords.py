import itertools

def build_universal_scale(edo, generators, dimensions, chain_starts=None, tonic=0):
    """
    Generates the sequence of pitch classes in a scale.

    Args:
        edo: equal divisions of the octave; how many pitches are in one octave
        generators: A mathematical tool used to generate the scales.
        dimensions: the number of notes along each axis. E.g. for diatonic scales, is `[7]`; for pentatonic scales, is `[5]`.
        chain_starts: the initial note along each axis. Effectively controls the mode, e.g. with diatonic scales, `[-1]` for Ionian and `[-4]` for Aeolian.
        tonic: amount mod `edo` to add to each of the notes. `0` by default. E.g. for getting the `D` instead of `C` major diatonic scale, `tonic` should be `2`.

    Returns:
        A dictionary specifying:
        - EDO: input argument
        - Pitches: sorted list of pitches between 0 and EDO, e.g. for D major is [1, 2, 4, 6, 7, 9, 11]
        - Steps: the steps between each of the pitches
        - Step sizes:
        - Generators: input argument
    """
    if chain_starts is None:
        chain_starts = [0] * len(generators)

    axis_ranges = [range(start, start + dim) for start, dim in zip(chain_starts, dimensions)]
    pitches = set()
    
    for coords in itertools.product(*axis_ranges):
        pitch = sum(c * g for c, g in zip(coords, generators)) % edo
        pitches.add(pitch)

    # Apply tonic as a pure transposition after scale generation, so it
    # doesn't interact with the chain_starts mode offset.
    pitches = sorted([(p + tonic) % edo for p in pitches])
    steps = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]
    steps.append(edo - pitches[-1])
    unique_steps = sorted(list(set(steps)), reverse=True)

    return {
        "EDO": edo,
        "Pitches": pitches,
        "Steps": steps,
        "Step_Sizes": unique_steps,
        "Generators": generators
    }

def build_chords(scale_pitches, edo, chord_size=3, tonic=0):
    """
    Using the output of build_universal_scale, generate the set of scale degree chords.
    These are numbered with Roman numerals, which we use for defining chord progressions in `main.py`.

    Args:
        scale_pitches: the set of pitches in the scale
        edo: equal divisions of the octave
        chord_size: the number of notes in each chord. 3 is the default, 4 is for v7 chords.
        tonic: because the Pitches returned by `build_universal_scale` is sorted, we have to index into it to find the index of the actual first pitch, `tonic`.

    Returns:
        list of lists of integers representing pitch classes
    """
    n = len(scale_pitches)
    chords = []

    # Get the index of the tonic, as that should be the root of the first chord.
    if tonic in scale_pitches:
        tonic_idx = scale_pitches.index(tonic)
    else:
        tonic_idx = 0

    for degree in range(n):
        root_idx = (tonic_idx + degree) % n
        chord = []
        for k in range(chord_size):
            # TODO might want to allow flexibility in the 2 for non-12 EDO scales
            degree_idx = (root_idx + 2 * k) % n
            pitch = scale_pitches[degree_idx]
            chord.append(pitch)
        chords.append(chord)
        
    return chords

# def print_tonnetz_shape(chord, edo, generators):
#     """
#     Prints an ASCII visualizer of the Tonnetz grid centered on the chord's root.
#     Highlights chord tones with [ ] to show their geometric shape.
#     """
#     root = chord[0]
#     g1 = generators[0]
#     g2 = generators[1] if len(generators) > 1 else 0
    
#     print("    Tonnetz Geometry:")
    
#     if g2 == 0:
#         # 1D Chain Visualization (Prints from -2 to +5 generators away)
#         # Most MOS triads form a block at x=0, x=1, and x=4.
#         row_str = "    Axis: "
#         for x in range(-2, 6):
#             pitch = (root + x * g1) % edo
#             if pitch in chord:
#                 row_str += f"[{pitch:2d}] "
#             else:
#                 row_str += f" {pitch:2d}  "
#         print(row_str)
#     else:
#         # 2D Grid Visualization (5x5 grid)
#         for y in range(2, -3, -1):
#             row_str = "    "
#             for x in range(-2, 3):
#                 pitch = (root + x * g1 + y * g2) % edo
#                 if pitch in chord:
#                     row_str += f"[{pitch:2d}] "
#                 else:
#                     row_str += f" {pitch:2d}  "
#             print(row_str)


if __name__ == "__main__":
    scales_to_test = {
        #
        # 1D moment of symmetry (MOS) scales
        #

        "12-EDO Diatonic (Major)": {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1]},
        "12-EDO Pentatonic":       {"edo": 12, "generators": [7], "dimensions": [5], "chain_starts": [0]},
        "19-EDO Meantone":         {"edo": 19, "generators": [11], "dimensions": [7], "chain_starts": [-1]},
        
        #
        # 2D scales
        #

        # Blackwood: 5 blocks of 3 steps. Inside block: 2 notes separated by 2. 
        # Results in [2, 1, 2, 1...] pattern in 15-EDO
        "15-EDO Blackwood (10-note)": {"edo": 15, "generators": [3, 2], "dimensions": [5, 2], "chain_starts": [0, 0]},
        
        # Octatonic: 4 blocks of 3 steps. Inside block: 2 notes separated by 2.
        # Results in a perfect [2, 1, 2, 1...] pattern in 12-EDO
        "12-EDO Octatonic (Diminished)": {"edo": 12, "generators": [3, 2], "dimensions": [4, 2], "chain_starts": [0, 0]},
        
        # Whole Tone: 6 blocks of 2 steps.
        "12-EDO Whole Tone": {"edo": 12, "generators": [2], "dimensions": [6], "chain_starts": [0]},

        #
        # Other
        #

        # 5-Limit Hexatonic: Stacking P5ths (7) and M3rds (4)
        "12-EDO 5-Limit Hexatonic": {"edo": 12, "generators": [7, 4], "dimensions": [3, 2], "chain_starts": [0, 0]},
        "31-EDO Diatonic (Extended Meantone)": 
            {"edo": 31, "generators": [18], "dimensions": [7], "chain_starts": [-1]},
        "16-EDO Mavila (Anti-Diatonic)": 
            {"edo": 16, "generators": [9], "dimensions": [7], "chain_starts": [-1]},
        # 15-EDO Blackwood properly mapped as a 2D repeating block to prevent the crash
        "15-EDO Blackwood (10-note)": 
            {"edo": 15, "generators": [3, 2], "dimensions": [5, 2], "chain_starts": [0, 0]},
        "22-EDO Porcupine (7-note)": 
            {"edo": 22, "generators": [3], "dimensions": [7], "chain_starts": [0]},
        "19-EDO Magic (10-note)": 
            {"edo": 19, "generators": [6], "dimensions": [10], "chain_starts": [0]},
    }

    # numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

    # for name, params in scales_to_test.items():
    #     print(f"{'='*50}")
    #     print(f"{name.upper()}")
    #     print(f"{'='*50}")
        
    #     scale = build_universal_scale(**params)
    #     print(f"Pitches:    {scale['Pitches']}")
    #     print(f"Step Sizes: {scale['Step_Sizes']}\n")
        
    #     chords = build_chords(scale['Pitches'], scale['EDO'], chord_size=3)
        
    #     for i, chord in enumerate(chords):
    #         label = numerals[i] if i < len(numerals) else str(i + 1)
    #         print(f"  {label} Chord: {chord}")
    #         print_tonnetz_shape(chord, scale['EDO'], scale['Generators'])
    #         print()