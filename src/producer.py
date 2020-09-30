import os
import music21 as m2
import sox
import attr
import singer
import song
# from singer import Singer
# from song import Song

@attr.s()
class Producer(object):
    """
    holds objects of Song and Singer, and contains some util functions.
    """
    song_settings=attr.ib(type=dict)
    singer_settings=attr.ib(type=dict)

    # 
    # init functions
    #
    def __attrs_post_init__(self):
        self.song = song.Song(**self.song_settings)
        self.singer = singer.Singer(**self.singer_settings)
    

    #
    # static methods
    #
    @staticmethod
    def render_audio(midi_path, audio_path, soundfont_path="../downloads/FluidR3Mono_GM.sf3", gain=0.7, chorus=0, reverb=0, verbose=True):
        """
        Renders the input midi file to an audio file using fluidsynth and a specified soundfont.
        instrument and note assignments follows the General MIDI (GM) protocol.

        There are two simple effects included in MIDI GM, chorus and reverb, but we can only control the on/off, not the mix.
        """
        stream = os.popen(f"fluidsynth {soundfont_path} {midi_path} -F {audio_path} -g {gain} --chorus {chorus} --reverb {reverb} -o synth.min-note-length=1000")
        output = stream.read()
        if verbose:
            print(output)


    @staticmethod
    def merge_midi(midi_in_1_path: str, midi_in_2_path: str, midi_out_path: str):
        """
        merge two midi files.

        does not work with mma-generated midi files. instruments and quantization has some error.
        works well with music21 outputs.
        """

        s1 = m2.converter.parse(midi_in_1_path, format="midi", quantizePost=False)
        s2 = m2.converter.parse(midi_in_2_path, format="midi", quantizePost=False)
        s1.mergeElements(s2)
        print(s1.elements[1].elements)
        # s1.write("midi", midi_out_path)
        # print(f"midi file written at {midi_out_path}")
    

    @staticmethod
    def merge_audio(audio_in_1_path: str, audio_in_2_path: str, mix: float, audio_out_path: str):
        """
        merge two audio files using pysox.
        does not support .oga file.

        Parameters
        ----------
        mix: ratio of audio_in_1

        """

        comb = sox.combine.Combiner()
        comb.set_input_format(file_type=["wav", "wav"])
        comb.build([audio_in_1_path, audio_in_2_path], audio_out_path, "mix", [mix, 1-mix])


    #
    # class methods
    #
    def build(self, output_path="../producer_output.wav", remove_temp=True):
        """
        build the final output .wav file.

        Parameters
        ----------
        remove_temp: whether to remove all the temp files.

        """
        os.mkdir("../temp/")

        self.song.build("../temp/output.mma") # generates the accompany midi file
        self.singer.sing_interval(4, 10, 0.2) 
        self.singer.export_midi("../temp/singer_output.mid") # generates the melody midi file
        Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../temp/output.mid", audio_path="../temp/output.wav", verbose=True)
        Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../temp/singer_output.mid", audio_path="../temp/singer_output.wav", verbose=True)
        Producer.merge_audio("../temp/output.wav", "../temp/singer_output.wav", mix=0.5, audio_out_path=output_path)

        print(f"audio file exported at {output_path}")

        if remove_temp:
            os.remove("../temp/output.mid")
            os.remove("../temp/output.wav")
            os.remove("../temp/singer_output.mid")
            os.remove("../temp/singer_output.wav")
            os.rmdir("../temp")


if __name__ == "__main__":
    cp = "D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n"
    song_settings = {"name": "my song",
                    "genre": "pop",
                    "tempo": 110,
                    "chord_progression": cp,
                    "pattern_progression": [5, 8, 15]}

    singer_settings = {"tempo": 110,
                       "key": "D",
                       "time_signature": "4/4", 
                       "chord_progression": cp,
                       "pattern_progression": [5, 9, 13]}

    my_producer = Producer(song_settings, singer_settings)
    my_producer.build()