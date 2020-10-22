"""
Last modified: 21 Oct, 2020
Author: Arthur Jinyue Guo jg5505@nyu.edu
"""
import os
import attr
import json
import numpy as np
import music21 as m2

@attr.s()
class SingerBase(object):
    """
    The base class of melody generators. Must implement self.sing() method to generate melody.

    Attributes
    ----------
    tempo : int
        the BPM
    key : str
        key signature in music21 format.
    chord_progression : str
        e.g. "D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\n", "D\nBm\nG\nA7\n"
    pattern_prograssion: str
        currently not used
    instrument : str
        must be in instruments.json/"supported_instruments"
        the instrument to use when generating midi file. Names are defined in General Midi protocol.
        supported instruments (must be exact name): https://web.mit.edu/music21/doc/moduleReference/moduleInstrument.html
    key: str
        the key signature of the tune. Affects self.possible_pitches.
    time_signature: str
        the time signature.
    instrument_path: str
        path to instruments.json, which contains instrument configs.
    sound_range: tuple
        Sound range of the singer. Inclusive on both end.
    with_chords: bool
        Whether to append the chords to the Stream. 
        will generate a piano accompaniment in the output midi file.
    defaul_volume: int
        The defaul volume of the singer, in range [1, 127].

    # note generator shared settings
    # recommend setting: speed=4/8/16, rand_vol=10, rand_trig=0.2
    speed : int
        must be power of 2, usually between 2 and 32.
    rand_vol : int
        range of random volume (0 to 127)
    rand_trig : float
        a possibility of notes being muted, 0 to 1 (0 will trigger all notes, 1 mutes all)
    """
    tempo = attr.ib(type=int)
    chord_progression = attr.ib(type=str)
    pattern_progression = attr.ib(type=list)
    instrument = attr.ib(type=str, default="Violin")
    key = attr.ib(type=str, default="C")
    time_signature = attr.ib(type=str, default="4/4")
    instrument_path = attr.ib(type=str, default="./instruments.json")
    sound_range = attr.ib(type=tuple, default=('C4', 'G5'))
    with_chords = attr.ib(type=bool, default=False)
    default_volume = attr.ib(type=int, default=90)
    # sing() parameters
    speed = attr.ib(type=int, default=4)
    rand_vol = attr.ib(type=int, default=10)
    rand_trig = attr.ib(type=float, default=0.2)

    #
    # init functions 
    #
    def __attrs_post_init__(self):
        # load instrument config file
        with open(self.instrument_path, "r") as f:
            f_json = json.load(f)
            supported_instruments = f_json["supported_instruments"]
            instruments = f_json["instruments"]
    
        if self.instrument not in supported_instruments:
            raise ValueError(f"Unsupported instrument: {self.instrument}")

        self.inst_settings = instruments[self.instrument]

        # init the main stream object
        self.s = m2.stream.Stream([m2.tempo.MetronomeMark(number=self.tempo), 
                                m2.key.Key(self.key), 
                                m2.meter.TimeSignature(self.time_signature)])
        self.instrument_class = getattr(m2.instrument, self.instrument)
        self.melody = m2.stream.Part([self.instrument_class()])
        self.chords = m2.stream.Part([m2.instrument.Piano()])

        self.num_measures = len(self.chord_progression.split("\n")[:-1])
        for chord in self.chord_progression.split("\n")[:-1]:
            c = m2.harmony.ChordSymbol(chord, duration=4)
            c.volume = m2.volume.Volume(velocity=70)
            self.chords.append(c)

        self.s.append(self.melody)
        if self.with_chords:
            self.s.append(self.chords)

        # all the possible pitches within the sound range and in the key.
        self.possible_pitches = self.s.keySignature.getScale().getPitches(self.inst_settings["sound_range_low"], self.inst_settings["sound_range_high"])

    @tempo.validator
    def check_tempo(self, attribute, value):
        if value < 40 or value > 250:
            raise ValueError(f"Invalid tempo value: {value}")

    @default_volume.validator
    def check_vol(self, attribute, value):
        if value < 0 or value > 127:
            raise ValueError(f"Invalid default volume: {value}")

    @pattern_progression.validator
    def check_pp(self, attribute, value):
        if len(value) != 4:
            raise ValueError(f"Invalid pattern progression length: {len(value)}")
        if value[0] < 0 or value[1] < 0 or value[2] < 0 or value[3] < 0 or \
           value[1] < value[0] or value[2] < value[1] or value[2] < value[0] or \
           value[3] < value[2] or value[3] < value[1] or value[3] < value[0]:
           raise ValueError(f"Invalid pattern progression value: {value}")

        num_chords = len(self.chord_progression.split("\n"))-1
        if value[0] > num_chords or value[1] > num_chords or \
           value[2] > num_chords or value[3] > num_chords:
           raise ValueError(f"Invalid pattern progression, \must be smaller than chord progression : {value}")


    #
    # class methods
    #
    def sing(self):
        """
        The virtual function of sing. generates the melody line, fills self.melody function.
        """
        raise NotImplementedError()

    def export_midi(self, midi_path, write_chords=False):
        """
        """
        if (write_chords is True) and (self.with_chords is False):
            self.s.append(self.chords)
        self.s.write("midi", midi_path)
        print(f"midi file written at {midi_path}")


class MusicTheoryError(Exception):
    """
    Error message of music theory. such as chord not in the key, etc.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# A sample of test main function.
# Does not work for this base class, but you can use this if you override SingerBase.sing()
if __name__ == "__main__":
    my_singer = Singer(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])

    my_singer.sing()
    my_singer.export_midi("../singer_output.mid", write_chords=False)
    Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../singer_output.mid", audio_path="../singer_output.wav", verbose=True)