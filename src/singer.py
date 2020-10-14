#Last modified: 14 Oct, 2020
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
                supported instruments (must be exact name): https://web.mit.edu/music21/doc/moduleReference/moduleInstrument.html
                recommended: Violin, Flute, TenorSaxophone, ...

    # note generator settings
    # recommend setting: speed=4/8/16, rand_vol=10, rand_trig=0.2
    speed: must be power of 2, usually between 2 and 32.
    rand_vol: range of random volume (0 to 127)
    rand_trig: a possibility of notes being muted, 0 to 1 (0 will trigger all notes, 1 mutes all)
    """

    tempo = attr.ib(type=int)
    chord_progression = attr.ib(type=str)
    pattern_progression = attr.ib(type=list)
    instrument = attr.ib(type=str, default="Violin")
    key = attr.ib(type=str, default="C")
    time_signature = attr.ib(type=str, default="4/4")
    instrument_path = attr.ib(type=str, default="./instruments.json")
    sound_range = attr.ib(type=tuple, default=('C4', 'G5'))
    # note generation attrs
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
        instrument_class = getattr(m2.instrument, self.instrument)
        self.melody = m2.stream.Part([instrument_class()])
        self.chords = m2.stream.Part([m2.instrument.Piano()])

        for chord in self.chord_progression.split("\n")[:-1]:
            c = m2.harmony.ChordSymbol(chord, duration=4)
            c.volume = m2.volume.Volume(velocity=70)
            self.chords.append(c)
        
        self.s.append(self.melody)
        # self.s.append(self.chords)

        # all the possible pitches within the sound range and in the key.
        self.possible_pitches = self.s.keySignature.getScale().getPitches(self.inst_settings["sound_range_low"], self.inst_settings["sound_range_high"])

    @tempo.validator
    def check_tempo(self, attribute, value):
        if value < 40 or value > 250:
            raise ValueError(f"Invalid tempo value: {tempo}")

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
    def sing_chord(self):
        """
        a singer who only sings the chord pitches. fills self.melody.
            basically same as a random arppegiator.
        """
        default_volume = 90
        speed = np.random.choice(self.inst_settings["speed"])
        for current_chord in self.chords.elements:
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
                    n.volume = m2.volume.Volume(velocity=default_volume+int(self.inst_settings["rand_vol"]*(2*np.random.rand()-1)))
                n.duration = m2.duration.Duration(4/speed)

                self.melody.append(n)


    def sing_interval(self):
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

            for i in range(int(speed*int(self.time_signature[0])/4)):
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
        target_pitch: music21.interval.Interval object.
        pitch_list: list of strings, each string is a pitch name, e.g. "G4"
        prob_factor: the index of reverse probability. if bigger, the closer note will have higher probability.
        prob_offset: offset when calculating inversed probability.

        Returns
        -------
        interval_p: the normalized probability of each note.
        """
        interval_to_rf = np.array([np.abs(m2.interval.Interval(target_pitch, m2.pitch.Pitch(p)).semitones) for p in pitch_list])
        interval_p = 1 / (interval_to_rf + prob_offset)
        interval_p = interval_p ** prob_factor
        interval_p = interval_p / np.sum(interval_p)
        return interval_p


if __name__ == "__main__":
    my_singer = Singer(tempo=110, key="D", time_signature="4/4", 
                       instrument="TenorSaxophone",
                       chord_progression="D\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\nD\nBm\nG\nA7\n",
                       pattern_progression=[5, 8, 9, 13])
    
    my_singer.sing_interval()
    my_singer.export_midi("../singer_output.mid", write_chords=False)
    Producer.render_audio(soundfont_path="../downloads/Orpheus_18.06.2020.sf2", midi_path="../singer_output.mid", audio_path="../singer_output.wav", verbose=True)