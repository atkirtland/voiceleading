# Solving for equal temperament voice leadings

TLDR: We allow for synthesizing voice leadings (specifically a set of notes, one for each of four voices) given an initial chord and chord progression within some scale. The scale is defined in a general way using moment of symmetry scales that support microtonal, equal temperament tuning systems.

This was originally developed as a project for Brown [CSCI 1710](https://csci1710.github.io/2026/).

## Code outline

- `chords.py` specifies functions to generate scales (`build_scale`). These are then used to build scale degree chords (`build_chords`), which are the chords denoted with Roman numerals in the music literature. We use capital letters for all scale degrees, though the literature uses lowercase letters for minor chords, and has extra symbols for diminished and augmented chords.
- `main.py` defines `generate_efficient_voice_leading` which uses Z3 to optimize for a voice leading that minimizes a distance metric. It takes as input chords given by `build_chords`, and uses as a helper function `get_valid_midi_notes`.
- `display.py` outputs standard MIDI + MusicXML with `export_to_music21`, and microtonal MIDI with `export_microtonal_midi`. The other functions in the file are helper functions or unused functions (see the comments as needed).
- There are test files for each of these.
- The examples using `generate_efficient_voice_leading` along with the functions from `chords.py` are in `examples/`.

### How to run the model

The code was tested on Python 3.9.25. Install requirements with `pip install -r requirements.txt`. MIDI files and musicxml files are output to `outputs/`. If you want to open the musicxml files, you need to install software like [MuseScore Studio](https://musescore.org/en/download), and you need to change the path variable set in `display.py` with the location of your installation. 

The 12-EDO (just intonation) MIDI files can be opened with any standard MIDI player. Microtonal music may not be played correctly with all MIDI players due to the pitch bends, but one piece of software that can play it correctly is [FluidSynth](https://github.com/FluidSynth/fluidsynth) with commands such as `fluidsynth -a alsa /usr/share/sounds/sf2/FluidR3_GM.sf2 output/test_31edo_chromatic_microtonal.mid`.

The core set of examples can be run with `python examples/<filename>` from the root directory by uncommenting the code of the desired example. The tests can be run with `python main_tests.py`, `python chords_tests.py`, and `python display_tests.py`.


## Background math

Some relevant vocabulary:
- Voice: a linear sequence of notes
- Chord: a set of notes played at once.
- Voice leading: an ordered set of voices, which defines a chord at each timestep. We typically have 4 voices present, bass, tenor, alto, and soprano.
- Scale: A linear sequence of notes that loops back to the beginning
- Scale degree chords: Chords produced from scales. The $n$th scale degree chord is produced by taking the $n$th scale note and stacking on it the $n+2$th and $n+4$th notes in the scale (mod scale length) to produce a chord.
- [Equal divisions of the octave (EDO) = equal temperament](https://en.xen.wiki/w/Equal-step_tuning): these are the microtonal tuning sytems we support. Essentially, instead of dividing an octave (a set of pitches that range from $f_0$ to $2f_0$, i.e. a doubling in pitch) into 12 pieces, $n$-EDO systems divide them into $n$ pieces.
- [Moment of symmetry scales](https://en.xen.wiki/w/MOS_scale): we use this framework, generalized to 2+ dimensions, to generate scales in `chords.py`. These essentially just generate a linear sequence of tones in an EDO system given a set of basic mathematical data. We choose this system because it is general and relatively simple.
- [Counterpoint](https://en.wikipedia.org/wiki/Counterpoint): we implement a couple of counterpoint rules to attempt to constrain the voice leading synthesis to be more interesting. However, we do not make this an emphasis of the project (in part because it was the suggested project idea of another team on EdStem), nor do we follow any particular set of counterpoint rules. We did not do analysis as to how the synthesized music changes with the inclusion/exclusion of the counterpoint rules.

## Goals

Foundational
- [x] Implement a basic set of constraints defining voice leadings with Z3. This involves optimizing the solution set for shortest distance leadings.
- [x] Visualize the results on a music staff.
- [x] Synthesize multiple voice leadings to write a few lines / a simple piece of music. Or try to synthesize voice leadings from the music literature with this algorithm.
    - We have a few examples. 
        - `pachelbel.py` synthesizes a line of music with the bass line being Pachelbel's canon. 
        - `circle-of-fifths.py` synthesizes a circle of fifth of chords in C Major. 
        - `cmaj.py` synthesizes a basic C major chord progression (C Major (I) -> A Minor (vi) -> F Major (IV) -> G Major (V) -> C Major (I)).
        - `31edo.py` synthesizes a chord progression in 31-EDO, a microtonal tuning system.
- [/] Test how different distance metrics produce different types of leadings.
    - We have implemented both L1 and L2 distance metrics. However, because Z3 is not guaranteed to produce globally optimal solutions under nonlinear optimization targets, the L2 metric as currently implemented produces suboptimal results. To fully explore this question, we can instead implement it as a linearized constraint by explicitly restricting the distance a voice can move on each timestep and adding these in split cases. 
- [/] Visualize the results in pitch space on a Tonnetz, an alternate representation in a triangulated space.
    - We have experimental code for visualizing scale degrees on a Tonnetz that is currently commented out.
- [x] Define alternate tuning systems to compute voice leadings over. e.g. microtonal systems such as 19-EDO (equal divisions of the octave), 24-EDO, or just intonation.
    - We allow for arbitrary $n$-EDO tuning systems. Voice leadings synthesized in these systems are output via MIDI with pitch bends, and can be listened with a synthesizer like `fluidsynth` (mentioned above in the run instructions).
- [/] Search instead for other music structures in these tuning systems, such as counterpoint or comma pumps.
    - We implement counterpoint rules to refine the voice leading synthesis.
    - Analyzing comma pumps involves looking at the actual frequencies of the notes within an $n$-EDO system. For example, in $n$-EDO, the $k$th semitone above the base frequency $f_0$ has frequency $f_02^{k/n}$. We use this kind of math in the voice leading synthesis for calculating the number of semitones that constitutes a fifth as a function of $n$, namely by solving $\log_2(3/2)=k/n$. For example, with $n=12$, $k\approx 7$. However, we are interested in furthering this with work that judges potential microtonal patterns by whether they produce approximate integer ratios.

We could also have defined the scales and scale degree chords in Z3 along with the voice leadings.

### AI Use

Gemini Pro generated much of the code via prompting.
