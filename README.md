# Solving for equal temperament voice leadings

TLDR: We allow for synthesizing voice leadings (specifically a set of notes, one for each of four voices) given an initial chord and chord progression within some scale. The scale is defined in a general way using moment of symmetry scales that support microtonal, equal temperament tuning systems.

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

We achieve the foundational goals and have partial progress on all target and reach goals. Our understanding of the feasibility of these goals changed somewhat through the course of the project as we learned more about the underlying math and Z3 solver constraints.

Foundational
- [x] Implement the basic set of constraints defining voice leadings with Z3. This involves optimizing the solution set for shortest distance leadings.
- [x] Visualize the results on a music staff.

Target
- [x] Synthesize multiple voice leadings to write a few lines / a simple piece of music. Or try to synthesize voice leadings from the music literature with this algorithm.
    - We have a few examples. 
        - One synthesizes a line of music with the bass line being Pachelbel's canon. 
        - Another example synthesizes a circle of fifth of chords in C Major. 
        - Another synthesizes a basic C major chord progression (C Major (I) -> A Minor (vi) -> F Major (IV) -> G Major (V) -> C Major (I)).
        - Another synthesizes a chord progression in 31-EDO, a microtonal tuning system.
- [/] Test how different distance metrics produce different types of leadings.
    - We have implemented both L1 and L2 distance metrics. However, because Z3 is not guaranteed to produce globally optimal solutions under nonlinear optimization targets, the L2 metric as currently implemented produces suboptimal results. To fully explore this question, we can instead implement it as a linearized constraint by explicitly restricting the distance a voice can move on each timestep and adding these in split cases. However, we did not do this because of time constraints. 
- [/] Visualize the results in pitch space on a Tonnetz, an alternate representation in a triangulated space.
    - We have experimental code for visualizing scale degrees on a Tonnetz that is currently commented out.

Reach
- [x] Define alternate tuning systems to compute voice leadings over. e.g. microtonal systems such as 19-EDO (equal divisions of the octave), 24-EDO, or just intonation.
    - We allow for arbitrary $n$-EDO tuning systems. Voice leadings synthesized in these systems are output via MIDI with pitch bends, and can be listened with a synthesizer like `fluidsynth` (mentioned below in the run instructions).
- [/] Search instead for other music structures in these tuning systems, such as counterpoint or comma pumps.
    - We implement counterpoint rules to refine the voice leading synthesis.
    - Analyzing comma pumps involves looking at the actual frequencies of the notes within an $n$-EDO system. For example, in $n$-EDO, the $k$th semitone above the base frequency $f_0$ has frequency $f_02^{k/n}$. We use this kind of math in the voice leading synthesis for calculating the number of semitones that constitutes a fifth as a function of $n$, namely by solving $\log_2(3/2)=k/n$. For example, with $n=12$, $k\approx 7$. However, we are interested in furthering this with work that judges potential microtonal patterns by whether they produce approximate integer ratios.

We could have instead defined the scales and scale degree chords in Z3 along with the voice leadings. We did not do that due to time constraints though.

## Modeling choices

Bucket 1: Core
- What a voice leading is, and basic constraints for it.
- Distance as a function of a voice leading

Bucket 2: not critical
- Defining scales: we do this in general Python, not Z3.
- Defining chords given a scale: we do this in general Python, not Z3.
- Counterpoint rules for voice leadings: we do some of these.

Bucket 3: can be abstracted away
- For the most part, handling frequencies explicitly can be abstracted away in favor of just handling MIDI integer values. However, this is an interesting area of further work, and, actually, handing fifths in a microtonal system in a general way requires doing math with frequencies.
- Non-EDO microtonal tuning systems. I think these would generally require using frequencies explicitly, and it seems like they would be complicated to incorporate with the current math. In the current setup, I was able to generalize many parts of `main.py` to EDO scales by replacing `12` with `edo`, but this wouldn't work for non-EDO systems.

## How to run the model

Tested on Python 3.9.25, install requirements with `pip install -r requirements.txt`. MIDI files and musicxml files are output to `outputs/`. If you want to open the musicxml files, you need to install software like [MuseScore Studio](https://musescore.org/en/download), and you need to change the path variable set in `display.py` with the location of your installation. 

The 12-EDO (just intonation) MIDI files can be opened with any standard MIDI player. Microtonal music may not be played correctly with all MIDI players due to the pitch bends, but one piece of software that can play it correctly is [FluidSynth](https://github.com/FluidSynth/fluidsynth) with commands such as `fluidsynth -a alsa /usr/share/sounds/sf2/FluidR3_GM.sf2 output/test_31edo_chromatic_microtonal.mid`.

The core set of examples can be run with `python examples/<filename>` from the root directory by uncommenting the code of the desired example. The tests can be run with `python main_tests.py`, `python chords_tests.py`, and `python display_tests.py`.

## Takeaways

The project was quite educational for music theory and Z3. In terms of music theory, I now have a much clearer idea of how generalized moment of symmetry scales are calculated from generators, how these define a set of pitches, how the pitches define a set of scale degree chords, how scale degree chord pitches define allowable chords in a voice leading, and how counterpoint and other basic voice leading rules modulate voice leadings. The same math here works for all equal divisions of the octave microtonal systems.

I also learned about basic optimization of Z3 specifications, namely
- Replacing modulo with `Or` statements given a finite set of possibilities.
- Replacing basic L1 distance calculations with a dummy/ghost variable to use arithmetic inequalities instead of logical implies.

In terms of interesting information that the modeling itself yielded, I think trying to recreate Pachelbel's canon revealed something interesting, that an additional constraint is required to produce the right bass line, as well as restricting the bass voice within a certain range. I added this as a general `extra_constraints` argument to the Z3 synthesis function with the idea that synthesizing other musical lines would require similar one-off constraints.

## Collaboration

I did not collaborate with any humans, although Siddhartha provided suggestions during the Design Checks.

### AI Use

I used Gemini Pro for generating much of the code given prompts such as "I would like to enforce traditional counterpoint rules to produce more interesting music. Can you suggest how to add them into the code below? <pasted main.py>", where `main.py` already had the synthesis working with the basic, non-counterpoint constraints. I also used it for getting suggestions on optimizing the Z3 code and for questions such as which microtonal structures would be reasonable to support. My Gemini chat history is turned off, so I am unable to provide the exact prompts used. 

However, I have reviewed all of the code, I wrote the comments myself (except for repetitive comments like labeling chord progressions), and I restructured the code/logic several times to be more readable. The only exception to this is `display.py`, which uses the `music21` and `mido` libraries to output to musicxml and MIDI. I am not very familiar with these libraries, and it seems acceptable to rely on the LLM's judgement here as this is outside of the core modeling task. My verification of the correctness of the code comes from listening to the produced MIDI files and `display_test.py`.

I also used Sonnet 4.6 with Cursor for edits like properly formatting docstrings (while keeping my own written text, as I verified) due to the convenient diff displays. My prompts to Cursor were similar to my prompts to Gemini, and to the best of my ability, I tried to contain its edits to only a single file at a time. Essentially, the only difference is that the edits were applied automatically via diffs instead of copy and pasted in to the code.