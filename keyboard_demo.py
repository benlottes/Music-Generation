import time
import pygame
import pygame.midi
import math
from json import load

from music21 import *
from midi_util import produce_note_strings, convert_to_midi

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

def print_midi_info():
    # pygame.midi.init()
    for i in range(pygame.midi.get_count()):
        print(pygame.midi.get_device_info(i))
    
    print("Default in: ", pygame.midi.get_default_input_id())
    print("Default out: ", pygame.midi.get_default_output_id())
    # pygame.midi.quit()

def num_to_note(num):
    note = NOTES[num % 12]
    note = note + str(math.ceil(num/12)-1)
    return note

def take_input(i, o):#(in_id = None, out_id = None):
    # if not in_id:
    #     in_id = pygame.midi.get_default_input_id()

    # if not out_id:
    #     out_id = pygame.midi.get_default_output_id()
    
    while(i.read(1)):
        pass

    o.set_instrument(0)

    pygame.display.set_mode((1,1))
    note_count = 0

    #Format: [[pitch, start, stop], [pitch,start,stop], ...]
    note_seq = [] 
    duration_seq = []
    while note_count < 8:
        if i.poll(): #if a note has been presseed
            midi_event = i.read(1) #grab note played

            if midi_event[0][0][0] == 144: #if note on
                #print(midi_event)
                print(num_to_note(midi_event[0][0][1]))
                note = midi_event[0][0][1]
                time_stamp = midi_event[0][1] # in milliseconds I think

                if len(note_seq) < 8:
                    note_seq.append([note, time_stamp, 0])

                o.note_on(note, 120)               

            if midi_event[0][0][0] == 128: #if note off
                #print(midi_event)
                note = midi_event[0][0][1]
                time_stamp = midi_event[0][1]
                for n in range(len(note_seq)-1, -1, -1):
                    if(note_seq[n][0] == note and note_seq[n][2] == 0):
                        note_seq[n][2] = time_stamp
                o.note_off(note, 120)
               
                note_count += 1  #DOES NOT ACCOUNT FOR CHORDS
    for j in note_seq:
        duration_seq.append(j[2]-j[1])

    #print(note_seq)
    #print(duration_seq)
    time.sleep(1) #Give last note time to play

    while len(note_seq) < 8:
        note_seq.append(note_seq[-1])
        
    return note_seq



if __name__ == "__main__":
    pygame.midi.init()
    pygame.mixer.init()
    print_midi_info()

    json_file = open("int_to_note.json")

    int_to_note = load(json_file)
    note_to_int = {v: k for k, v in int_to_note.items()}

    in_id, out_id = 1, 2
    i = pygame.midi.Input(in_id)
    o = pygame.midi.Output(out_id,latency=0)#,buffer_size=1)

    while 1:
        note_seq = take_input(i, o)

        user_notes_int = []
        user_notes_str = []
        for note in note_seq:
            pitch = note[0]
            note_str = num_to_note(pitch)

            if note_str not in note_to_int:
                if len(user_notes_int) > 0:
                    note_str = user_notes_str[-1]
                else:
                    note_str = "C3"
            user_notes_int.append(int(note_to_int[note_str]))
            user_notes_str.append(note_str)

        # print(user_notes_int)
        print("User inputted notes: ", user_notes_str)

        predicted_notes_str = produce_note_strings(user_notes_int, int_to_note, n_notes=8)[len(user_notes_int):]
        print("Model predicted notes:", predicted_notes_str)

        # play those notes
        
        convert_to_midi(predicted_notes_str, ["quarter"] * len(predicted_notes_str), "songs/keyboard_demo.mid")
        pygame.mixer.music.load("songs/keyboard_demo.mid")
        pygame.mixer.music.play()


    i.close()
    o.close()
    pygame.midi.quit()
    pygame.quit()