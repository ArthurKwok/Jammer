"""
Last modified: 21 Oct, 2020
Author: Arthur Jinyue Guo jg5505@nyu.edu
"""
import os
import attr
import json
import numpy as np
import music21 as m2

from singer_base import SingerBase

@attr.s()
class SingerA(SingerBase):
    """
    A simple singer that is basically an arpeggiator with chord tones.
    """

    # override SingerBase.sing()
    def sing(self):
        """
        a singer who only sings the chord pitches. fills self.melody.
        basically same as a random arppegiator.
        """
        speed = np.random.choice(self.inst_settings["speed"])
        for current_chord in self.chords.elements[1:]:
            chord_tones = [pitch.name for pitch in current_chord.pitches]
            singable_pitches = []
            for pitch in self.possible_pitches:
                if pitch.name in chord_tones:
                    singable_pitches.append(pitch.nameWithOctave)

            for i in range(int(speed*int(self.time_signature[0])/4)):
                if np.random.rand() < self.inst_settings["rand_trig"]:
                    n = m2.note.Rest()
                else:
                    current_pitch = np.random.choice(singable_pitches)
                    n = m2.note.Note(current_pitch)
                    n.volume = m2.volume.Volume(velocity=self.default_volume+int(self.inst_settings["rand_vol"]*(2*np.random.rand()-1)))
                n.duration = m2.duration.Duration(4/speed)

                self.melody.append(n)

if __name__ == "__main__":
    my_singer = SingerA(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])
    
    my_singer.sing()
    print(my_singer.melody.elements)