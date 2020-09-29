import os

class Producer():

    @staticmethod
    def render_audio(soundfont_path, midi_path, audio_path, gain=0.7, chorus=0, reverb=0, verbose=True):
        if soundfont_path is None:
            soundfont_path = "../downloads/FluidR3Mono_GM.sf3"
        stream = os.popen(f"fluidsynth {soundfont_path} {midi_path} -F {audio_path} -g {gain} --chorus {chorus} --reverb {reverb} -o synth.min-note-length=1000")
        output = stream.read() 
        if verbose:
            print(output)
