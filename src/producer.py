#Last modified: 14 Oct, 2020
#Author: Arthur Jinyue Guo jg5505@nyu.edu

import os
import sox
import attr
import json
import numpy as np
import music21 as m2

import singer
import song

@attr.s()
class Producer(object):
    """
    holds objects of Song and Singer, and contains some util functions.
    """
    # song_settings = attr.ib(type=dict)
    # singer_settings = attr.ib(type=dict)
    key = attr.ib(type=str)
    genre_name = attr.ib(type=str)
    leadsheet_path = attr.ib(type=str, default="./leadsheets.json")

    # 
    # init functions
    #
    def __attrs_post_init__(self):
        with open(self.leadsheet_path, "r") as f:
            f_json = json.load(f)
            supported_genres = f_json["supported_genres"]
        
        if self.genre_name not in supported_genres:
            raise ValueError(f"Unsupported genre: {self.genre_name}")

        genre = f_json["genres"][self.genre_name]
        
        # Using lead sheet settings to generate Song and Singer settings
        # generate chord progression
        chord_prog, pattern_prog = self.gen_chord_prog(self.key, genre["chord_progression"])
        tempo = self.choose_tempo(genre["tempo_range"])
        singer_instrument = np.random.choice(genre["singer_instruments"])

        song_settings = {"name": "my song",
                        "genre": self.genre_name,
                        "tempo": tempo,
                        "chord_progression": chord_prog,
                        "pattern_progression": pattern_prog}

        singer_settings = {"tempo": tempo,
                        "key": self.key,
                        "time_signature": np.random.choice(genre["time_signature"]), 
                        "chord_progression": chord_prog,
                        "pattern_progression": pattern_prog,
                        "instrument": singer_instrument}

        # instantiate Song and Singer member
        self.song = song.Song(**song_settings)
        self.singer = singer.Singer(**singer_settings)


    #
    # static methods
    #
    @staticmethod
    def render_audio(midi_path: str, audio_path: str, soundfont_path="../downloads/FluidR3Mono_GM.sf3", gain=0.7, chorus=0, reverb=0, verbose=True):
        """
        Renders the input midi file to an audio file using fluidsynth and a specified soundfont.
        instrument and note assignments follows the General MIDI (GM) protocol.

        There are two simple effects included in MIDI GM, chorus and reverb, but we can only control the on/off, not the mix.

        Parameters
        ----------
        gain: the master gain. default value is 0.3 for fluidsynth, which is too small.
        chorus: a binary boolean controlling the chorus switch. CAN NOT BE FLOAT!
        reverb: a binary boolean controlling the reverb switch. CAN NOT BE FLOAT!
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
    def gen_chord_prog(self, key, chord_progressions):
        """
        Genrates chord progression according to the leadsheet.

        returns
        -------
        chord_prog: a string
        pattern_prog: a list with four ints like [5, 7, 8, 15]
        """
        chord_prog = ""
        pattern_prog = []

        chord_prog += np.random.choice(chord_progressions["Intro"])
        pattern_prog.append(len(chord_prog.split("\n")))
        chord_prog += np.random.choice(chord_progressions["Main1"])
        pattern_prog.append(len(chord_prog.split("\n")))
        chord_prog += np.random.choice(chord_progressions["Fill"])
        pattern_prog.append(len(chord_prog.split("\n")))
        chord_prog += np.random.choice(chord_progressions["Main2"])
        pattern_prog.append(len(chord_prog.split("\n")))
        chord_prog += np.random.choice(chord_progressions["Outro"])

        return chord_prog, pattern_prog

    def choose_tempo(self, tempo_range):
        """
        Randomly choose a tempo in the range.
        """
        return np.random.randint(tempo_range[0], tempo_range[1])

    def build(self, mix=0.5, output_path="../producer_output.wav", remove_temp=True):
        """
        build the final output .wav file.

        Parameters
        ----------
        remove_temp: whether to remove all the temp files.

        """
        try:
            os.mkdir("../temp/")
        except:
            pass

        self.song.build("../temp/output.mma") # generates the accompany midi file
        self.singer.sing_interval() 
        self.singer.export_midi("../temp/singer_output.mid") # generates the melody midi file
        Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../temp/output.mid", audio_path="../temp/output.wav", verbose=True)
        Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../temp/singer_output.mid", audio_path="../temp/singer_output.wav", verbose=True)
        Producer.merge_audio("../temp/output.wav", "../temp/singer_output.wav", mix=mix, audio_out_path=output_path)

        print(f"audio file exported at {output_path}")

        if remove_temp:
            os.remove("../temp/output.mid")
            os.remove("../temp/output.wav")
            os.remove("../temp/singer_output.mid")
            os.remove("../temp/singer_output.wav")
            os.rmdir("../temp")


if __name__ == "__main__":
    my_producer = Producer(key="D", genre_name="waltz")
    my_producer.build(mix=0.5, remove_temp=True)
    # cp = "D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n"
    # song_settings = {"name": "my song",
    #                 "genre": "pop",
    #                 "tempo": 110,
    #                 "chord_progression": cp,
    #                 "pattern_progression": [5, 8, 15]}

    # singer_settings = {"tempo": 110,
    #                    "key": "D",
    #                    "time_signature": "4/4", 
    #                    "chord_progression": cp,
    #                    "pattern_progression": [5, 9, 13],
    #                    "instrument": "TenorSaxophone"}
    #                 #    "instrument": "Violin"}