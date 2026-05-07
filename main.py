"""
This file contains the core modeling code, and defines how to synthesize a voice leading from a list of scale degree chords and an initial chord.
"""
import math
from z3 import *


def get_valid_midi_notes(pitch_class, min_midi, max_midi, edo=12):
    """Given an EDO, returns MIDI keys within a pitch class between a minimum and maximum specified specified value."""
    return [note for note in range(min_midi, max_midi + 1) if note % edo == pitch_class]

def generate_efficient_voice_leading(start_chord, progression_pcs, metric="L1", ranges=None, optimize=True, extra_constraints=None, edo=12):
    """
    Args:
        start_chord: the chord in MIDI numbers (e.g. 60 for C4)
        progression_pcs: the sequence of pitch classes the voices must be in at each time step
        metric: L1, L2 (not guaranteed to find global minima, only a feasible solution due to Z3), or Linf (unimplemented)
        ranges: specified MIDI ranges allowed for each voice. Useful for optimization and replicating known pieces.
        optimize: whether to use Optimize or Solve (with a heuristic). Solve is faster, but Optimize yields much better solutions and is not too slow.
        extra_constraints: additional Z3 constraits used in the examples to achieve results resembling known works. E.g. for synthesizing something like Pachelbel's canon, this constrains the bass line.
        edo: how many units we divide the octave into.

    Returns:
        a sequence of 4 MIDI pitches at each timestep that lie within the progression_pcs pitch classes, begin with start_chord, and optimize the specifie metric.
    """

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

    # contains MIDI values for each voice for each timestep
    voices = [[Int(f'v_{t}_{v}') for v in range(num_voices)] for t in range(num_chords)]

    # constrain the initial chord
    for v in range(num_voices):
        opt.add(voices[0][v] == start_chord[v])

    #
    # Constraints
    #

    # for each timestep
    for t in range(num_chords):

        # Disallow voice crossing
        for v in range(num_voices-1):
            opt.add(voices[t][v] < voices[t][v+1])
    
        # Restrict voices to lie within the ranges specified by `ranges`
        for v in range(num_voices):
            minv, maxv = ranges[v]
            opt.add(And(voices[t][v] >= minv, voices[t][v] <= maxv))

        target_pcs = progression_pcs[t]

        # For the following two conditions, we started by writing a simple constraint with modulo, but then to speed up the calculations, we converted it to a linearized version using `get_valid_midi_notes`. I listed both versions below, with the modulo one commented out, as the modulo one is easier to understand.

        # # Every voice must be in one of the target pitch classes
        # for v in range(num_voices):
        #     opt.add(Or([voices[t][v] % edo == pc for pc in target_pcs]))
        for v in range(num_voices):
            minv, maxv = ranges[v]
            valid_note_conditions = []
            for pc in target_pcs:
                valid_notes = get_valid_midi_notes(pc, minv, maxv, edo=edo)
                for note in valid_notes:
                    valid_note_conditions.append(voices[t][v] == note)
            opt.add(Or(valid_note_conditions))

        # # Every pitch in the target pitch class must be occupied by some voice.
        # for pc in target_pcs:
        #     opt.add(Or([voices[t][v] % edo == pc for v in range(num_voices)]))
        for pc in target_pcs:
            pc_present_conditions = []
            for v in range(num_voices):
                min_val, max_val = ranges[v]
                valid_notes = get_valid_midi_notes(pc, min_val, max_val, edo=edo)
                for note in valid_notes:
                    pc_present_conditions.append(voices[t][v] == note)
            opt.add(Or(pc_present_conditions))
    
        #
        # Traditional counterpoint rules
        #

        # Upper adjacent voices are at most one octave apart
        opt.add(voices[t][2] - voices[t][1] <= edo)
        opt.add(voices[t][3] - voices[t][2] <= edo)

        if t > 0:
            # The tonic is the root of the first chord in the progression. 
            # The leading tone is the tone just before the tonic.
            # This counterpoint rule requires that if the tonic is present in a chord in the progression after the first timestep, then if a voice has a leading tone on the previous timestep, it must resolve to the tonic.

            tonic_pc = progression_pcs[0][0]
            leading_tone_pc = (tonic_pc - 1) % edo
            next_chord_pcs = progression_pcs[t]
            resolves_to_tonic = tonic_pc in next_chord_pcs
            if resolves_to_tonic:
                for v in range(num_voices):
                    minv, maxv = ranges[v]
                    leading_tone_notes = get_valid_midi_notes(leading_tone_pc, minv, maxv, edo=edo)
                    for lt_note in leading_tone_notes:
                        opt.add(Implies(
                            voices[t-1][v] == lt_note,
                            voices[t][v] == lt_note + 1
                        ))

            # For adjacent voices, forbid parallel fifths and octaves. I.e. the bass and tenor lines cannot both move a fifth up at the same time.

            # calculates what a perfect fifth should be in the EDO system.
            # in 12-EDO yields 7
            perfect_fifth = round(edo * math.log2(3 / 2))
            for i in range(num_voices - 1):
                j = i + 1
                prev_i = voices[t-1][i]
                prev_j = voices[t-1][j]
                curr_i = voices[t][i]
                curr_j = voices[t][j]
                both_moved = And(curr_i != prev_i, curr_j != prev_j)

                prev_diff = prev_j - prev_i
                curr_diff = curr_j - curr_i
                max_diff = ranges[j][1] - ranges[i][0]

                for interval in [perfect_fifth, edo]:
                    parallel_conditions = []
                    for d in range(interval, max_diff + 1, edo):
                        parallel_conditions.append(
                            And(prev_diff == d, curr_diff == d)
                        )
                    if parallel_conditions:
                        opt.add(Implies(both_moved, Not(Or(parallel_conditions))))


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

            # Dummy variable for the distance travelled by voice `v`
            dist_var = Int(f'dist_{t}_{v}')

            if metric == "L1":
                # dist_var must be >= both the positive and negative movement.
                opt.add(dist_var >= movement1)
                opt.add(dist_var >= movement2)

            elif metric == "L2":
                # because this is nonlinear, if it is used, Z3 is not guaranteed to find a global minima, only a solution within the feasible set 
                opt.add(dist_var == movement1 * movement1)
                
            elif metric == "Linf":
                pass

            step_distances.append(dist_var)

    # Add this check in to cover the edge case of a single timestep progresion (should be only the start chord)
    if step_distances:
        total_distance = Sum(step_distances)

        if optimize:
            opt.minimize(total_distance)
        else:
            if metric == "L1":
                # Allow an average of 3 semitones per voice per step
                max_acceptable_distance = num_voices * (num_chords - 1) * 3
            elif metric == "L2":
                max_acceptable_distance = num_voices * (num_chords - 1) * 9

            # satisfice
            opt.add(total_distance <= max_acceptable_distance)
    else:
        total_distance = IntVal(0)

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