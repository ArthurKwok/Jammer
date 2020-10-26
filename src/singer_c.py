"""
Last modified: 23 Oct, 2020
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
    continue_develop = attr.ib(type=bool, default=True)
    motif_length = attr.ib(type=int, default=2)
    prob_factor = attr.ib(type=float, default=2)
    prob_offset = attr.ib(type=float, default=5)

    # override SingerBase.sing()
    def sing(self):
        """
        """
        # Intro: append one rest note
        rest_quarter_length = (self.pattern_progression[0] - 1) * int(self.time_signature[0])
        self.melody.append(m2.note.Rest(quarterLength=rest_quarter_length))

        # Main1: generate a motif, append motif, then generate modifications until beginnig of Main2
        chord_index = (self.pattern_progression[0] - 1) + (self.motif_length) - 1
        motif = self._generate_motif()
        self.melody.append(motif.elements)
        while chord_index + self.motif_length < self.pattern_progression[1]:
            variation = self._modify_motif(motif, self.chords.elements[chord_index:chord_index+self.motif_length])
            self.melody.append(variation.elements)
            chord_index += self.motif_length
            if self.continue_develop:
                motif = variation
        
        # Main2: same as main1, generate until outro
        chord_index = (self.pattern_progression[2] - 1) + (self.motif_length) - 1
        motif = self._generate_motif()
        self.melody.append(motif.elements)
        while chord_index + self.motif_length < self.pattern_progression[3]:
            variation = self._modify_motif(motif, self.chords.elements[chord_index:chord_index+self.motif_length])
            self.melody.append(variation.elements)
            chord_index += self.motif_length
            if self.continue_develop:
                motif = variation

    def _generate_motif(self)->m2.stream.Part:
        """
        Generate a motif with length of self.num_measures
        Basically the same as SingerB.sing().
        """
        motif = m2.stream.Part()
        self.speed = np.random.choice(self.inst_settings["speed"])
        for current_chord in self.chords.elements[1:self.motif_length+1]:
            chord_tones = [pitch.name for pitch in current_chord.pitches]
            singable_pitches = []
            for pitch in self.possible_pitches:
                if pitch.name in chord_tones:
                    singable_pitches.append(pitch.nameWithOctave)

            if singable_pitches is None:
                raise MusicTheoryError(f"No singable pitches! chord: {current_chord}, key: {self.key}")

            for i in range(int(self.speed * int(self.time_signature[0])/4)):
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
                n.duration = m2.duration.Duration(4/self.speed)

                motif.append(n)
        return motif

    #TODO
    def _modify_motif(self, original_motif, chord_progression):
        """
        modify the original motif according to a probability distribution notes_prob.
        the distribution is an exponential function parameterized by base and offset.
        base and offset are randomly generated each time.

        After notes_prob is generated, roll a dice to decide which notes are to be modified (notes_to_modify)

        When modifying, randomly choose among four types of modifications

        Parameters
        ----------
        original_motif : music21.stream.Part
        chord_progression : list of music21.harmony.ChordSymbol
        """
        modified_motif = copy.deepcopy(original_motif)
        num_notes = len(modified_motif)

        # set prob distribution parameters
        # base = np.random.choice(range(2, 10))
        # offset = np.random.choice(range(0, 16))
        base = 5 * np.random.rand() + 1.1
        offset = 3 * np.random.rand() + 0.1
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
            if type(target_note) is m2.note.Rest:
                continue
            #randomly choose one modification:
            #0. if the note is not chord tone, change it to a chord tone;
            #   if it is, change it to a none chord tone but key tone.
            #1. change note to a diatonic passing tone
            #2. change note to the same as the next tone
            #3. change note to key's 1, 3 or 5
            modify_mode = np.random.choice(range(4))
            if modify_mode == 0:
                #0. if the note is not chord tone, change it to a chord tone;
                #   if it is, change it to a none chord tone but key tone.
                current_chord = chord_progression[int(i/self.speed)]
                chord_tones = [pitch.name for pitch in current_chord.pitches]
                singable_pitches = []
                for pitch in self.possible_pitches:
                    if pitch.name in chord_tones:
                        singable_pitches.append(pitch)
                if target_note.pitch not in current_chord.pitches:
                    target_note.pitch = self._nearest_pitch(target_note.pitch, singable_pitches)
                else:
                    target_note.pitch = self._nearest_pitch(target_note.pitch, self.possible_pitches)

            elif modify_mode == 1:
                #1. change note to a diatonic passing tone
                next_note = modified_motif.getElementAfterElement(target_note, [m2.note.Note])
                prev_note = modified_motif.getElementBeforeOffset(target_note.offset, [m2.note.Note])
                if next_note is None or prev_note is None:
                    continue
                target_pitch = m2.pitch.Pitch((next_note.pitch.midi + prev_note.pitch.midi) / 2)
                target_pitch = self._nearest_pitch(target_pitch, self.possible_pitches)
                target_note.pitch = target_pitch

            elif modify_mode == 2:
                #2. change note to the same as the next tone or prev note
                next_note = modified_motif.getElementAfterElement(target_note, [m2.note.Note])
                if next_note is None:
                    continue
                target_note.pitch = next_note.pitch

            elif modify_mode == 3:
                #3. change note to key's 1, 3 or 5
                target_note.pitch =self._nearest_pitch(target_note.pitch, self.s.keySignature.getScale().pitchesFromScaleDegrees([1,3,5], self.inst_settings["sound_range_low"], self.inst_settings["sound_range_high"]))

        return modified_motif

    #
    # util funcs
    #
    def _interval_reversed_p(self, target_pitch:m2.interval.Interval, pitch_list: list, prob_factor=2, prob_offset=5)->list:
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


    def _position_exponential_p(self, num_notes: int, prob_base: float, prob_offset: float)->list:
        """
        Generates a probability distribution that, later notes have higher probability to be changed.
        
        Parameters
        ----------
        num_notes : int
        prob_base : float
        prob_offset : float

        Returns
        -------
        notes_prob : list of float
            the normalized probability. All between 0 and 1.
        """
        notes_prob = np.power(prob_base, (np.arange(1+prob_offset, num_notes+1+prob_offset))/num_notes)
        ## normalize probability
        notes_prob = notes_prob / (np.max(notes_prob)+prob_offset)

        return list(notes_prob)

    def _nearest_pitch(self, target_pitch: m2.pitch.Pitch, pitch_list: list)->list:
        """
        Return the nearest pitch to target_pitch in pitch_list.

        Parameters
        ----------
        target_pitch : music21.pitch.Pitch
            pitch with octave.
        pitch_list : list of music21.pitch.Pitch
            pitch with octave
        
        Returns
        -------
        nearest_pitch : music21.pitch.Pitch
        """
        if len(pitch_list) == 0:
            raise ValueError(f"Pitch List is Empty!")

        # if target_pitch is in pitch_list, remove it
        for pitch in pitch_list:
            if pitch.nameWithOctave == target_pitch.nameWithOctave:
                pitch_list.remove(pitch)

        interval_to_rf = np.array([np.abs(m2.interval.Interval(target_pitch, pit).semitones) for pit in pitch_list])
        return pitch_list[np.argmin(interval_to_rf)]


if __name__ == "__main__":
    my_singer = SingerC(tempo=110, key="D", time_signature="4/4", 
                       instrument="Piano",
                       motif_length=2,
                       prob_factor=4,
                       default_volume=100,
                       continue_develop=True,
                       chord_progression="D\nBm\nG\nA7\n"+
                                         "D\nBm\nG\nA7\n"+
                                         "D\nBm\nG\nA7\n"+
                                         "D\nBm\nG\nA7\n"+
                                         "D\nBm\nG\nA7\n"+
                                         "D\nD\nD\nD\nD\n",
                       pattern_progression=[5, 12, 13, 17])
    
    my_singer.sing()
    # print(my_singer.melody.elements)
    my_singer.export_midi("../singer_output.mid", write_chords=True)
    from producer import Producer
    Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../singer_output.mid", audio_path="../singer_output.oga", verbose=True)