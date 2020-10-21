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
    Singer that considers the previous note. 
    Note with smaller interval to the previous note will have higher probablity to be chosen.

    Parameters
    ----------
    prob_factor : float
        Parameter of SingerB._interval_reversed_p().
        the index of reverse probability. if bigger, the closer note will have higher probability.
    prob_offset : float
        Parameter of SingerB._interval_reversed_p().
        offset when calculating inversed probability.
    """
    prob_factor = attr.ib(type=float, default=2)
    prob_offset = attr.ib(type=float, default=5)

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
                        interval_p = self._interval_reversed_p(self.melody.notes[-1].pitch, 
                                                              singable_pitches,
                                                              self.prob_factor,
                                                              self.prob_offset)
                        try:
                            current_pitch = np.random.choice(singable_pitches, p=interval_p)
                        except:
                            raise ValueError(f"Random choice failed! chord: {current_chord}, key: {self.key}")
                    n = m2.note.Note(current_pitch)
                    n.volume = m2.volume.Volume(velocity=default_volume+int(self.inst_settings["rand_vol"]*(2*np.random.rand()-1)))
                n.duration = m2.duration.Duration(4/speed)

                self.melody.append(n)

    def _interval_reversed_p(self, target_pitch, pitch_list, prob_factor=2, prob_offset=5)->list:
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


if __name__ == "__main__":
    my_singer_b = SingerB(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])
    
    my_singer_b.sing()
    print(my_singer_b.melody.elements)