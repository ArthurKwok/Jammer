"""
Last modified: 20 Oct, 2020
Author: Arthur Jinyue Guo jg5505@nyu.edu
"""
import os
import attr
import json
import numpy as np
import music21 as m2

from singer_base import SingerBase

@attr.s()
class SingerB(SingerBase):
    """
    A simple singer that is basically an arpeggiator with chord tones.

    Parameters
    ----------
    speed : int
        must be power of 2, usually between 2 and 32.
    rand_vol : int
        range of random volume (0 to 127)
    rand_trig : float
        a possibility of notes being muted, 0 to 1 (0 will trigger all notes, 1 mutes all)

    # recommend setting: speed=4/8/16, rand_vol=10, rand_trig=0.2
    """
    speed = attr.ib(type=int, default=4)
    rand_vol = attr.ib(type=int, default=10)
    rand_trig = attr.ib(type=float, default=0.2)

    # override SingerBase.sing()
    def sing(self):
        """
        Sing according to interval with the previous note. closer note will have higher probability.
        """
        default_volume = 90
        speed = np.random.choice(self.inst_settings["speed"])
        for current_chord in self.chords.elements[1:]:
            chord_tones = [pitch.name for pitch in current_chord.pitches]
            singable_pitches = []
            for pitch in self.possible_pitches:
                if pitch.name in chord_tones:
                    singable_pitches.append(pitch.nameWithOctave)

            if singable_pitches is None:
                raise ValueError(f"No singable pitches! chord: {current_chord}, key: {self.key}")

            for i in range(int(speed * int(self.time_signature[0])/4)):
                if np.random.rand() < self.inst_settings["rand_trig"]:
                    n = m2.note.Rest()
                else:
                    if len(self.melody.notes) == 0:
                        current_pitch = np.random.choice(singable_pitches)
                    else:
                        interval_p = self.interval_reversed_p(self.melody.notes[-1].pitch, singable_pitches)
                        try:
                            current_pitch = np.random.choice(singable_pitches, p=interval_p)
                        except:
                            raise ValueError(f"Random choice failed! chord: {current_chord}, key: {self.key}")
                    n = m2.note.Note(current_pitch)
                    n.volume = m2.volume.Volume(velocity=default_volume+int(self.inst_settings["rand_vol"]*(2*np.random.rand()-1)))
                n.duration = m2.duration.Duration(4/speed)

                self.melody.append(n)

if __name__ == "__main__":
    my_singer_b = SingerB(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])
    
    my_singer_b.sing()
    print(my_singer_b.melody.elements)