#Last modified: 25 Sep, 2020
#Author: Arthur Jinyue Guo jg5505@nyu.edu

import os
import attr
import json
import numpy as np
import music21 as m2


@attr.s()
class Singer(object):
    """Generates the melody. outputs a midi file contrains single track of melody.

    Parameters
    ----------
    tempo: the BPM
    key: key signature in music21 format.
    chord_progression: the chords in ROMAN NUMERAL relative to key.
    instrument: the instrument to use when generating midi file. Names are defined in General Midi protocol.
    """

    tempo = attr.ib(type=int)
    chord_progression = attr.ib(type=str)
    pattern_progression = attr.ib(type=list)
    instrument = attr.ib(type=str, default="Violin")
    key = attr.ib(type=str, default="C")
    time_signature = attr.ib(type=str, default="4/4")
    sound_range = attr.ib(type=tuple, default=('C4', 'G5'))

    #
    # init functions 
    #
    def __attrs_post_init__(self):
        # init the main stream object
        self.s = m2.stream.Stream([m2.instrument.Instrument(self.instrument),
                                # m2.tempo.MetronomeMark(self.tempo), 
                                m2.key.Key(self.key), 
                                m2.meter.TimeSignature(self.time_signature)])
        self.melody = m2.stream.Part()
        self.chords = m2.stream.Part()

        for chord in self.chord_progression.split("\n")[:-1]:
            self.chords.append(m2.harmony.ChordSymbol(chord))
        
        self.s.append(self.melody)
        # self.s.append(self.chords)

        # all the possible pitches within the sound range and in the key.
        self.possible_pitches = self.s.keySignature.getScale().getPitches(self.sound_range[0], self.sound_range[1])

    @tempo.validator
    def check_tempo(self, attribute, value):
        if value < 40 or value > 250:
            raise ValueError(f"Invalid tempo value: {tempo}")

    @pattern_progression.validator
    def check_pp(self, attribute, value):
        if len(value) != 3:
            raise ValueError(f"Invalid pattern progression length: {len(value)}")
        if value[0] < 0 or value[1] < 0 or value[2] < 0 or \
           value[1] < value[0] or value[2] < value[1] or value[2] < value[0]:
           raise ValueError(f"Invalid pattern progression value: {value}")
        if value[0] > len(self.chord_progression.split("\n"))-1 or \
           value[1] > len(self.chord_progression.split("\n"))-1 or \
           value[2] > len(self.chord_progression.split("\n"))-1:
           raise ValueError(f"Invalid pattern progression, must be smaller than chord progression : {value}")
    
    
    #
    # class methods
    #
    def sing_chord(self, speed: int):
        """a singer who only sings the chord pitches. fills self.melody.
            basically same as a random arppegiator.

        Parameters
        ----------
        speed: must be power of 2, usually between 2 and 32.

        """
        for current_chord in self.chords.elements:
            chord_tones = [pitch.name for pitch in current_chord.pitches]
            singable_pitchs = []
            for pitch in self.possible_pitches:
                if pitch.name in chord_tones:
                    singable_pitchs.append(pitch.nameWithOctave)

            for i in range(speed):
                current_pitch = np.random.choice(singable_pitchs)
                self.melody.append(m2.note.Note(current_pitch, quarterLength=4/speed))


    def export_midi(self, midi_path, write_chords=False):
        """
        """
        if write_chords:
            self.s.append(self.chords)
        self.s.write("midi", midi_path)
        print(f"midi file written at {midi_path}")

if __name__ == "__main__":
    my_singer = Singer(tempo=110, key="D", time_signature="4/4", 
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 9, 13])
    
    my_singer.sing_chord(4)
    my_singer.export_midi("../singer_output.mid", write_chords=True)