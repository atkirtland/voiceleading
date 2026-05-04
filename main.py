from z3 import *
from display import export_to_music21, export_scala_file

def get_chord_pcs(numeral, root_pc=0, edo=12):
    # Example dictionary for 31-TET
    if edo == 31:
        harmony = {
            "I":   [0, 10, 18],     # Major
            "ii":  [5, 13, 23],     # Minor starting on step 5 (Major 2nd)
            "IV":  [13, 23, 31],    # Major starting on step 13 (Perfect 4th)
            "V":   [18, 28, 5],     # Major starting on step 18 (Perfect 5th)
        }
    elif edo == 12:
        harmony = {
            "I":    [0, 4, 7],     # Major (Root, M3, P5)
            "ii":   [2, 5, 9],     # Minor (M2, m3, P5)
            "iii":  [4, 7, 11],    # Minor (M3, m3, P5)
            "IV":   [5, 9, 12],    # Major (P4, M3, P5)
            "V":    [7, 11, 14],   # Major (P5, M3, P5)
            "V7":   [7, 11, 14, 17], # Dominant 7th (P5, M3, P5, m7)
            "vi":   [9, 12, 16],   # Minor (M6, m3, P5)
            "vii°": [11, 14, 17]   # Diminished (M7, m3, d5)
        }
        
    return [(pc + root_pc) % edo for pc in harmony[numeral]]

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
"""
def generate_efficient_voice_leading(start_chord, progression_pcs, metric="L1", ranges=None, optimize=False):

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

if __name__ == "__main__":
    # C Major in 4 voices: C3 (48), G3 (55), C4 (60), E4 (64)
    Cmaj = [48, 55, 60, 64]
    # F Major pitch classes: F=5, A=9, C=0
    Fmaj_pcs = [[48%12, 55%12, 64%12], [5, 9, 0]]

    # C Major (I) -> A Minor (vi) -> F Major (IV) -> G Major (V) -> C Major (I)
    # Cmajprog_pcs = [
    #     [0, 4, 7],  # Step 0: C, E, G
    #     [9, 0, 4],  # Step 1: A, C, E
    #     [5, 9, 0],  # Step 2: F, A, C
    #     [7, 11, 2], # Step 3: G, B, D
    #     [0, 4, 7]   # Step 4: C, E, G
    # ]
    progression = ["I", "vi", "IV", "V", "I"]
    # progression = ["I", "vi", "IV", "V"]
    Cmajprog_pcs = [get_chord_pcs(chord, root_pc=0, edo=12) for chord in progression]

    voice_ranges = {
        0: (36, 53), # Bass: C2 to F3
        1: (48, 65), # Tenor: C3 to F4
        2: (53, 72), # Alto: F3 to C5
        3: (60, 84)  # Soprano: C4 to C6
    }

    sequence_data = generate_efficient_voice_leading(Cmaj, Cmajprog_pcs, metric="L1", ranges=voice_ranges, optimize=True)
    export_to_music21(sequence_data, save_midi=True, display=True)
    export_scala_file(12, "12_EDO")

    # G2, D3, G3, B3
    Gmaj = [43, 50, 55, 59]
    # C, E, G
    Cmaj_pcs = [0, 4, 7]