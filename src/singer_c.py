"""
Last modified: 22 Oct, 2020
Author: Arthur Jinyue Guo jg5505@nyu.edu
"""
import os
import attr
import json
import copy
import numpy as np
import music21 as m2

from singer_base import SingerBase, MusicTheoryError

@attr.s()
class SingerC(SingerBase):
    """
    Singer that considers the previous note. 
    Note with smaller interval to the previous note will have higher probablity to be chosen.

    Parameters
    ----------
    continue_develop : bool
        If true, the last variation will be set as the new motif.
        If false, the motif will all be the same.
    motif_length : int
        The number of measure(s) of the motif.
    prob_factor : float
        Parameter of SingerB._interval_reversed_p().
        the index of reverse probability. if bigger, the closer note will have higher probability.
    prob_offset : float
        Parameter of SingerB._interval_reversed_p().
        offset when calculating inversed probability.
    """
    continue_develop = attr.ib(type=bool, default=False)
    motif_length = attr.ib(type=int, default=4)
    prob_factor = attr.ib(type=float, default=2)
    prob_offset = attr.ib(type=float, default=5)

    # override SingerBase.sing()
    def sing(self):
        """
        """
        measures_to_fill = self.num_measures
        motif = self._generate_motif()
        self.melody.append(motif.elements)

        measures_to_fill -= self.motif_length
        while measures_to_fill - self.motif_length >= 0:
            variation = self._modify_motif(motif)
            self.melody.append(variation.elements)
            measures_to_fill -= self.motif_length

    def _generate_motif(self)->m2.stream.Part:
        """
        Generate a motif with length of self.num_measures
        Basically the same as SingerB.sing().
        """
        motif = m2.stream.Part()
        speed = np.random.choice(self.inst_settings["speed"])
        for current_chord in self.chords.elements[1:self.motif_length+1]:
            chord_tones = [pitch.name for pitch in current_chord.pitches]
            singable_pitches = []
            for pitch in self.possible_pitches:
                if pitch.name in chord_tones:
                    singable_pitches.append(pitch.nameWithOctave)

            if singable_pitches is None:
                raise MusicTheoryError(f"No singable pitches! chord: {current_chord}, key: {self.key}")

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
                            raise MusicTheoryError(f"Random choice failed! Maybe the chord is not in the key. chord: {current_chord}, key: {self.key}")
                    n = m2.note.Note(current_pitch)
                    n.volume = m2.volume.Volume(velocity=self.default_volume+int(self.inst_settings["rand_vol"]*(2*np.random.rand()-1)))
                n.duration = m2.duration.Duration(4/speed)

                motif.append(n)
        return motif

    #TODO
    def _modify_motif(self, original_motif):
        """
        """
        modified_motif = copy.deepcopy(original_motif)
        num_notes = len(modified_motif)

        # set prob distribution parameters
        base = 16
        offset = 1
        # calculate prob distribution list
        notes_prob = self._position_exponential_p(num_notes, base, offset)
        # roll the dice and decide which notes should be modified
        notes_to_modify = []
        for i in range(num_notes):
            if np.random.rand() < notes_prob[i]:
                notes_to_modify.append(i)
        # shuffle order
        np.random.shuffle(notes_to_modify)
        # modify each note
        for i in notes_to_modify:
            target_note = modified_motif.elements[i]
            #randomly choose one modification:
            #0. if the note is not chord tone, change it to a chord tone;
            #   if it is, change it to a none chord tone but key tone.
            #1. change note to a diatonic passing tone
            #2. change note to the same as the next tone
            #3. change note to key's 1, 3 or 5
            modify_mode = np.random.choice(range(4))
            if modify == 0:
                #0. if the note is not chord tone, change it to a chord tone;
                #   if it is, change it to a none chord tone but key tone.
                pass
            elif modify == 1:
                #1. change note to a diatonic passing tone
                pass
            elif modify == 2:
                #2. change note to the same as the next tone
                pass
            elif modify == 3:
                #3. change note to key's 1, 3 or 5
                pass

        return modified_motif

    #
    # util funcs
    #
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


    def _position_exponential_p(self, num_notes, prob_base, prob_offset):
        notes_prob = np.power(base, (np.arange(1+offset, num_notes+1+offset))/num_notes)
        ## normalize probability
        notes_prob = notes_prob / (np.max(notes_prob)+offset)

        return notes_prob

if __name__ == "__main__":
    my_singer = SingerC(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       motif_length=2,
                       chord_progression="D\nBm\nG\nA7\n\
                                          D\nBm\nG\nA7\n\
                                          D\nBm\nG\nA7\n\
                                          D\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])
    
    my_singer.sing()
    print(my_singer.melody.elements)
    my_singer.export_midi("../singer_output.mid", write_chords=True)
    from producer import Producer
    Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../singer_output.mid", audio_path="../singer_output.oga", verbose=True)