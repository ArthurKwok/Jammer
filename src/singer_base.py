"""
Last modified: 20 Oct, 2020
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
    defaul_vaolume: int
        The defaul volume of the singer, in range [1, 127].
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
        if value[0] > num_chords or value[1] > num_chords or value[2] > num_chords or value[3] > num_chords:
           raise ValueError(f"Invalid pattern progression, must be smaller than chord progression : {value}")


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
        if write_chords:
            self.s.append(self.chords)
        self.s.write("midi", midi_path)
        print(f"midi file written at {midi_path}")

    @staticmethod
    def interval_reversed_p(target_pitch, pitch_list, prob_factor=2, prob_offset=5)->list:
        """
        calculate the interval of the pitch to each element in the pitch list.
        returns a normalized probability of each note, closer note has higher probability.

        Parameters
        ----------
        target_pitch : music21.interval.Interval 
            the targe pitch to calcualte interval with
        pitch_list : list of str
            each string is a pitch name, e.g. "G4"
        prob_factor : float
            the index of reverse probability. if bigger, the closer note will have higher probability.
        prob_offset : float
            offset when calculating inversed probability.

        Returns
        -------
        interval_p : list of float
            the normalized probability of each note.
        """
        interval_to_rf = np.array([np.abs(m2.interval.Interval(target_pitch, m2.pitch.Pitch(p)).semitones) for p in pitch_list])
        interval_p = 1 / (interval_to_rf + prob_offset)
        interval_p = interval_p ** prob_factor
        interval_p = interval_p / np.sum(interval_p)
        return interval_p


# if __name__ == "__main__":
#     my_singer = Singer(tempo=110, key="D", time_signature="4/4", 
#                        instrument="Piano",
#                        chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
#                        pattern_progression=[5, 8, 9, 13])

#     my_singer.sing()
#     # my_singer.export_midi("../singer_output.mid", write_chords=False)
#     # Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../singer_output.mid", audio_path="../singer_output.wav", verbose=True)