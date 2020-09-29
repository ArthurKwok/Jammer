import os
import music21 as m2

class Producer():

    @staticmethod
    def render_audio(midi_path, audio_path, soundfont_path="../downloads/FluidR3Mono_GM.sf3", gain=0.7, chorus=0, reverb=0, verbose=True):
        stream = os.popen(f"fluidsynth {soundfont_path} {midi_path} -F {audio_path} -g {gain} --chorus {chorus} --reverb {reverb} -o synth.min-note-length=1000")
        output = stream.read()
        if verbose:
            print(output)


    @staticmethod
    def merge_midi(midi_in_1_path: str, midi_in_2_path: str, midi_out_path: str):
        """
        merge two midi files.
        """

        s1 = m2.converter.parse(midi_in_1_path)
        s2 = m2.converter.parse(midi_in_2_path)
        s1.mergeElements(s2)
        s1.write("midi", midi_out_path)
        print(f"midi file written at {midi_out_path}")
