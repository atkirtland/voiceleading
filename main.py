from z3 import *
from display import export_to_music21, export_scala_file
from chords import build_universal_scale, build_chords


"""
Returns all MIDI notes matching a pitch class within a specific range.
Used for efficiency reasons, to avoid nonlinear modulo calculations.
"""
def get_valid_midi_notes(pitch_class, min_midi, max_midi, edo=12):
    return [note for note in range(min_midi, max_midi + 1) if note % edo == pitch_class]

"""
start_chord is the chord in MIDI numbers (e.g. 60 for C4)
metric determines how to optimize the voice leading
target_pcs are target pitch classes
extra_constraints: optional callback (solver, voices) -> None for per-example constraints
"""
def generate_efficient_voice_leading(start_chord, progression_pcs, metric="L1", ranges=None, optimize=False, extra_constraints=None):

    # specifies allowed MIDI key ranges for each voice.
    if not ranges:
        ranges = {
            0: (36, 84),
            1: (36, 84),
            2: (36, 84),
            3: (36, 84),
        }

    #
    # Basics
    #

    num_chords = len(progression_pcs)
    num_voices = len(start_chord)

    if optimize:
        opt = Optimize()
    else:
        opt = Solver()

    # array with midi numbers for each voice (bass, tenor, alto, soprano) for each timestep
    voices = [[Int(f'v_{t}_{v}') for v in range(num_voices)] for t in range(num_chords)]

    for v in range(num_voices):
        opt.add(voices[0][v] == start_chord[v])

    #
    # Constraints
    #

    for t in range(num_chords):

        #
        # Geometric constraints
        #

        # Prevent voice crossing to stay in the same "fundamental domain" of the musical space.
        for v in range(num_voices-1):
            opt.add(voices[t][v] < voices[t][v+1])
    
        # Restrict voices to a specific range to narrow search (and enforce validity within nonnegative bounds)
        for v in range(num_voices):
            minv, maxv = ranges[v]
            opt.add(And(voices[t][v] >= minv, voices[t][v] <= maxv))

        target_pcs = progression_pcs[t]

        # A. Every voice must be one of the target pitch classes
        # for v in range(num_voices):
        #     opt.add(Or([voices[t][v] % 12 == pc for pc in target_pcs]))
        for v in range(num_voices):
            minv, maxv = ranges[v]
            valid_note_conditions = []
            for pc in target_pcs:
                valid_notes = get_valid_midi_notes(pc, minv, maxv)
                for note in valid_notes:
                    valid_note_conditions.append(voices[t][v] == note)
            opt.add(Or(valid_note_conditions))

        # B. The chord must be complete (at least one root, one third, one fifth)
        # for pc in target_pcs:
        #     opt.add(Or([voices[t][v] % 12 == pc for v in range(num_voices)]))
        for pc in target_pcs:
            pc_present_conditions = []
            for v in range(num_voices):
                min_val, max_val = ranges[v]
                valid_notes = get_valid_midi_notes(pc, min_val, max_val)
                for note in valid_notes:
                    pc_present_conditions.append(voices[t][v] == note)
            opt.add(Or(pc_present_conditions))
    
        #
        # Traditional counterpoint rules
        #

        # # Rule A: No Voice Crossing (Geometry rule, but also classical)
        # for i in range(num_voices-1):
        #     opt.add(target_voices[i] < target_voices[i+1])

        # # Rule B: Spacing (Max an octave between adjacent upper voices)
        # # Tenor/Alto and Alto/Soprano should be <= 12 semitones apart.
        # opt.add(target_voices[2] - target_voices[1] <= 12)
        # opt.add(target_voices[3] - target_voices[2] <= 12)

        # # Rule C: Resolve the Leading Tone
        # # In G -> C, the note B (pitch class 11) MUST resolve up to C (+1 semitone)
        # for i in range(num_voices):
        #     if start_chord[i] % 12 == 11:
        #         opt.add(target_voices[i] == start_chord[i] + 1)

        # # Rule D: Forbid Parallel 5ths and Octaves
        # for i in range(3):
        #     for j in range(i+1, 4):
        #         start_interval = (start_chord[j] - start_chord[i]) % 12
                
        #         # If the starting interval is a perfect 5th (7) or octave (0)
        #         if start_interval == 7 or start_interval == 0:
        #             target_interval = (target_voices[j] - target_voices[i]) % 12
                    
        #             # Check if both voices actually moved
        #             v_i_moved = target_voices[i] != start_chord[i]
        #             v_j_moved = target_voices[j] != start_chord[j]
                    
        #             # If both moved, the target interval CANNOT be the same perfect interval
        #             opt.add(Implies(And(v_i_moved, v_j_moved), target_interval != start_interval))


    #
    # Per-example constraints
    #

    if extra_constraints:
        extra_constraints(opt, voices)

    #
    # Optimization
    #

    step_distances = []

    for t in range(num_chords - 1):
        for v in range(num_voices):
            movement1 = voices[t+1][v] - voices[t][v]
            movement2 = voices[t][v] - voices[t+1][v]

            # Create a dummy variable for the distance of this specific voice
            dist_var = Int(f'dist_{t}_{v}')

            if metric == "L1":
                # linearize the absolute value; Z3 doesn't require branching
                # dist_var must be >= both the positive and negative movement.
                opt.add(dist_var >= movement1)
                opt.add(dist_var >= movement2)

            elif metric == "L2":
                # squaring, which is nonlinear
                opt.add(dist_var == movement1 * movement1)
                
            elif metric == "Linf":
                # could be implemented with slack vars again
                pass

            step_distances.append(dist_var)

    total_distance = Sum(step_distances)

    if optimize:
        # OLD w/ nonlinear L1
        # loss = None
        # if metric == "L1":
        #     # We calculate the L1 norm (taxicab distance) between the start and target chords.
        #     def z3_abs(x):
        #         return If(x >= 0, x, -x)
        #     loss = z3_abs
        # elif metric == "L2":
        #     loss = lambda x: x**2
        # total_distance = Sum(Sum([loss(voices[t+1][v] - voices[t][v]) for v in range(num_voices)]) for t in range(num_chords-1))

        opt.minimize(total_distance)
    else:
        if metric == "L1":
            # Allow an average of 3 semitones per voice per step
            max_acceptable_distance = num_voices * (num_chords - 1) * 3
        elif metric == "L2":
            max_acceptable_distance = num_voices * (num_chords - 1) * 9 

        # satisficing instead of solving optimally
        opt.add(total_distance <= max_acceptable_distance)

    #
    # Solve and Output
    #

    if opt.check() == sat:
        model = opt.model()
        print("Optimized Sequence Trajectory:\n")

        sequence_data = []
        
        for t in range(num_chords):
            chord_voicing = [model[voices[t][v]].as_long() for v in range(num_voices)]
            sequence_data.append(chord_voicing)
            print(f"Step {t}: {chord_voicing}")
            
        print("\nTotal voice-leading work across sequence:", model.evaluate(total_distance).as_long())

        return sequence_data
    else:
        print("Unsatisfiable constraints.")

        return None

NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

if __name__ == "__main__":

    # # example 1: C major progression
    # diatonic_cmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 0}
    # scale_cmaj = build_universal_scale(**diatonic_cmaj)
    # chords_cmaj = build_chords(scale_cmaj["Pitches"], edo=12, chord_size=3, tonic=0)
    # diatonic_cmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_cmaj)}
    # # C Major (I) -> A Minor (vi) -> F Major (IV) -> G Major (V) -> C Major (I)
    # cmaj_progression = ["I", "VI", "IV", "V", "I"]
    # cmaj_pcs = [diatonic_cmaj_chords[numeral] for numeral in cmaj_progression]
    # Cmaj = [48, 55, 60, 64]  # C3 G3 C4 E4
    # voice_ranges = {
    #     0: (36, 53), # Bass: C2 to F3
    #     1: (48, 65), # Tenor: C3 to F4
    #     2: (53, 72), # Alto: F3 to C5
    #     3: (60, 84)  # Soprano: C4 to C6
    # }
    # sequence_data = generate_efficient_voice_leading(Cmaj, cmaj_pcs, metric="L1", ranges=voice_ranges, optimize=True)
    # export_to_music21(sequence_data, output_name="cmaj", save_midi=True, display=True)
    # export_scala_file(12, "12_EDO")

    # Pachelbel's Canon in D major
    diatonic_dmaj = {"edo": 12, "generators": [7], "dimensions": [7], "chain_starts": [-1], "tonic": 2}
    scale_dmaj = build_universal_scale(**diatonic_dmaj)
    chords_dmaj = build_chords(scale_dmaj["Pitches"], edo=12, chord_size=3, tonic=2)
    diatonic_dmaj_chords = {numeral: chord for numeral, chord in zip(NUMERALS, chords_dmaj)}

    pachelbel_progression = ["I", "V", "VI", "III", "IV", "I", "IV", "V"]
    pachelbel_pcs = [diatonic_dmaj_chords[numeral] for numeral in pachelbel_progression]
    # D major in 4 voices: D3(50), A3(57), D4(62), F#4(66)
    Dmaj = [50, 57, 62, 66]
    pachelbel_ranges = {
        0: (43, 54),  # Bass: D2 to F#3
        1: (50, 66),  # Tenor: D3 to F#4
        2: (54, 73),  # Alto: F#3 to C#5
        3: (62, 81),  # Soprano: D4 to A5
    }

    def pachelbel_constraints(opt, voices):
        # Pin the bass to the root of each chord (ground bass / basso ostinato)
        for t, chord_pcs in enumerate(pachelbel_pcs):
            root_pc = chord_pcs[0]
            bass_min, bass_max = pachelbel_ranges[0]
            bass_candidates = get_valid_midi_notes(root_pc, bass_min, bass_max)
            opt.add(Or([voices[t][0] == note for note in bass_candidates]))

    sequence_data = generate_efficient_voice_leading(Dmaj, pachelbel_pcs, metric="L1", ranges=pachelbel_ranges, optimize=True, extra_constraints=pachelbel_constraints)
    export_to_music21(sequence_data, output_name="pachelbel", save_midi=True, display=True)
    export_scala_file(12, "12_EDO")