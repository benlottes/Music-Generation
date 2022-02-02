import sys
import os
from music21 import *
import numpy as np
from keras.models import load_model
from typing import Union

#defining function to read MIDI files
def read_midi(file: str, allow_chords: bool) -> Union[np.ndarray, np.ndarray]:
    print("Loading Music File:", file)
    
    notes = []
    notes_to_parse = None
    durations = []

    #parsing a midi file
    try:
        midi = converter.parse(file)
    except Exception as e:
        print("Error:", e)
        return np.array([]), np.array([])

    #grouping based on different instruments
    s2 = instrument.partitionByInstrument(midi)

    if s2 == None:
        return np.array([]), np.array([])

    #Looping over all the instruments
    for part in s2.parts:
        print("Parsing Instrument:", str(part))
        #select elements of only piano
        if 'Piano' in str(part): 
            notes_to_parse = part.recurse() 

            #finding whether a particular element is note or a chord
            for element in notes_to_parse:
                #duration of the note or chord
                durations.append(element.duration.type)
                #note
                if isinstance(element, note.Note):
                    notes.append(str(element.pitch))
                #chord
                elif isinstance(element, chord.Chord):
                    if allow_chords:
                        notes.append('.'.join(str(n) for n in element.normalOrder))
                    else:
                        notes.append(str(element.pitches[0]))
                    

    print("Parsing Complete")
    return np.array(notes), np.array(durations)

def convert_to_midi(predicted_notes: list, predicted_durations: list, file_path: str = "song.mid") -> None:
    offset = 0
    output_notes = []

    # create note and chord objects based on the values generated by the model
    for pattern, dur in zip(predicted_notes, predicted_durations):
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                cn = int(current_note)
                new_note = note.Note(cn)
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)

            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            dur_obj = duration.Duration(type=dur)
            new_chord.duration = dur_obj
            output_notes.append(new_chord)
            
        # pattern is a note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            dur_obj = duration.Duration(type=dur)
            new_note.duration = dur_obj
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += 1
    midi_stream = stream.Stream(output_notes)
    midi_stream.write('midi', fp=file_path)


def produce_song(initial_note_seq: np.ndarray, initial_dur_seq: np.ndarray, x_int_to_note: dict, 
                x_int_to_dur: dict, n_notes: int = 10, midi_file_path: str = "song.mid") -> None:
    note_model = load_model('models/best_model_note.h5')
    duration_model = load_model('models/best_model_dur.h5')

    note_predictions = []
    duration_predictions = []
    for _ in range(n_notes):
        # create new note prediction
        note_probs = note_model.predict(initial_note_seq.reshape(1, -1, 1))[0]
        y_pred_note = np.argmax(note_probs, axis=0)
        note_predictions.append(y_pred_note)

        # create new duration prediction
        dur_probs = duration_model.predict(initial_dur_seq.reshape(1, -1, 1))[0]
        y_pred_dur = np.argmax(dur_probs, axis=0)
        duration_predictions.append(y_pred_dur)

        # insert new note and duration into sequence
        initial_note_seq = np.append(initial_note_seq.reshape(-1, 1), y_pred_note.reshape(-1, 1), axis=0)
        initial_dur_seq = np.append(initial_dur_seq.reshape(-1, 1), y_pred_dur.reshape(-1, 1), axis=0)
        # cut off the "oldest" note and duration
        initial_note_seq = initial_note_seq[1:]
        initial_dur_seq = initial_dur_seq[1:]

    print(note_predictions)
    print(duration_predictions)

    predicted_notes = [x_int_to_note[i] for i in note_predictions]
    predicted_durations = [x_int_to_dur[i] for i in duration_predictions]

    print(predicted_notes)
    print(predicted_durations)

    # print(predicted_notes)

    convert_to_midi(predicted_notes, predicted_durations, file_path=midi_file_path)

def mute():
    sys.stdout = open(os.devnull, 'w')

if __name__ == "__main__":
    notes, durations = read_midi("data/Begin The Beguine.mid")