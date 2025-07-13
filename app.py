#!/usr/bin/env python3

import asyncio
import interactive_terminal
import numpy as np
import selectors
import sounddevice as sd
import urwid

# Globals
octave = 4
piano_key_nr = 49
end_frequency_hz = 440.0
prev_sample = -0.5
prev_progress = 0.0
kick_mode_active = False
kick_start_frequency_hz = 5000
kick_frequency_hz = kick_start_frequency_hz
kick_hold_samples = int(44100 * 0.1)
kick_decay = 0.5
kick_finished_hold = False
kick_holding = False
nr_samples_kick_held = 0
waveform_type = "sine"


def piano_key_nr_to_string(piano_key_nr: int) -> str:
    note_strings = {
        0:  "C",
        1:  "C#",
        2:  "D",
        3:  "D#",
        4:  "E",
        5:  "F",
        6:  "F#",
        7:  "G",
        8:  "G'",
        9:  "A",
        10: "A#",
        11: "B",
    }
    octave = int((piano_key_nr + 8) / 12)
    note_index = (piano_key_nr + 8) % 12
    return f"{note_strings[note_index]}{octave}"

def keyboard_key_to_piano_key_nr(key: str) -> int:
    global octave

    note_index_from_keyboard_keys = {
        "A": 0,  # C
        "W": 1,  # C#
        "S": 2,  # D
        "E": 3,  # D#
        "D": 4,  # E
        "F": 5,  # F
        "T": 6,  # F#
        "G": 7,  # G
        "Y": 8,  # G#
        "H": 9,  # A
        "U": 10, # A#
        "J": 11, # B
        "K": 12, # C
    }

    if key.upper() not in note_index_from_keyboard_keys:
        return -1 # Something else can handle this key.

    note_index = note_index_from_keyboard_keys[key.upper()]
    note_index_root_c = octave * 12 - 8
    return note_index_root_c + note_index

def generate_waveform(samples_per_period,**kwargs):
    def sine(x):
        if kick_mode_active:
            return np.clip(4 * np.sin(x),-1.0,1.0)
        else:
            return np.sin(x)

    def saw(x):
        return x / np.pi - 1

    start = kwargs["start"] if "start" in kwargs else 0
    end = np.pi * 2

    nr_samples = int(samples_per_period * (1 - start / (2 * np.pi)))
    if nr_samples < 1:
        return np.array([])

    sample_indexes = np.linspace(start,end,nr_samples)
    if "waveform" not in kwargs or "waveform" in kwargs and kwargs["waveform"] == "sine":
        return np.apply_along_axis(sine,axis=0,arr=sample_indexes)
    elif "waveform" in kwargs and kwargs["waveform"] == "saw":
        return np.apply_along_axis(saw,axis=0,arr=sample_indexes)

def calculate_kick_decay(start_frequency_hz: float,end_frequency_hz: float,nr_samples: int):
    nr_samples_delta = 250
    decay_guess = 0.5
    while True:
        nr_samples_processed = 0
        frequency_hz = start_frequency_hz
        while frequency_hz > end_frequency_hz:
            samples_per_period = int(44100 / frequency_hz)
            nr_samples_processed += samples_per_period
            frequency_hz *= decay_guess
        if nr_samples_processed > nr_samples + nr_samples_delta:
            decay_guess -= 0.000001
        elif nr_samples_processed < nr_samples - nr_samples_delta:
            decay_guess += 0.000001
        else:
            return decay_guess

def piano_roll_callback(outdata,frames,time,status):
    global kick_decay
    global kick_hold_samples
    global kick_mode_active
    global kick_frequency_hz
    global kick_start_frequency_hz
    global end_frequency_hz
    global prev_progress
    global waveform_type

    global kick_finished_hold
    global kick_holding
    global nr_samples_kick_held

    if kick_frequency_hz < end_frequency_hz and kick_finished_hold == False:
        kick_holding = True
    if kick_frequency_hz < end_frequency_hz and kick_finished_hold:
        kick_finished_hold = False
        kick_holding = False
        nr_samples_kick_held = 0
        kick_frequency_hz = kick_start_frequency_hz

    if kick_mode_active:
        samples_per_period = int(44100 / kick_frequency_hz)
    else:
        samples_per_period = int(44100 / end_frequency_hz)

    # Generate the remainder of the waveform that was abandoned when we ran out of frames in the previous callback.
    remainder_waveform = generate_waveform(samples_per_period,start = prev_progress * np.pi * 2,waveform=waveform_type)
    full_waveform = generate_waveform(samples_per_period,waveform=waveform_type)

    remaining_samples_in_callback = frames

    # Start with the remainder.
    waveform = remainder_waveform
    remaining_samples_in_callback -= len(waveform)

    while remaining_samples_in_callback > samples_per_period:
        if kick_mode_active and kick_holding == False:
            samples_per_period = int(44100 / kick_frequency_hz)
            full_waveform = generate_waveform(samples_per_period=samples_per_period,waveform=waveform_type)
            kick_frequency_hz *= kick_decay
        elif kick_mode_active and kick_holding:
            nr_samples_kick_held += samples_per_period

        if kick_holding and nr_samples_kick_held > kick_hold_samples:
            kick_finished_hold = True
            kick_holding = False

        waveform = np.concatenate([waveform,full_waveform])
        remaining_samples_in_callback -= samples_per_period

    waveform = np.concatenate([waveform,full_waveform[0:remaining_samples_in_callback]])
    # We must abandon the waveform as we have run out of frames. Store our progress for the 
    # next callback so we can generate the remainder of the waveform in the next callback.
    prev_progress = remaining_samples_in_callback / samples_per_period

    if kick_mode_active:
        kick_frequency_hz *= kick_decay

    if kick_mode_active and kick_holding == False:
        kick_frequency_hz *= kick_decay
    elif kick_mode_active and kick_holding:
        nr_samples_kick_held += samples_per_period

    outdata[:] = waveform[:frames].reshape(frames,1)

async def task_finished():
    while stream_continue == True:
        await asyncio.sleep(0)

async def piano_roll_task():
    with sd.OutputStream(callback=piano_roll_callback,samplerate=44100,channels=1):
        await task_finished()

def piano_roll_activate(loop):
    global stream_continue
    global prev_sample

    prev_sample = -0.5

    stream_continue = True

    piano_roll_key_handler(loop,"foo")

    asyncio.create_task(piano_roll_task())

def piano_roll_deactivate(loop):
    global stream_continue

    stream_continue = False

def piano_roll_key_handler(loop,key):
    global kick_decay
    global kick_mode_active
    global end_frequency_hz
    global piano_key_nr
    global waveform_type
    global octave

    if key.upper() == "Z" and octave > 1:
        octave -= 1
        piano_key_nr -= 12
    if key.upper() == "X" and octave < 6:
        octave += 1
        piano_key_nr += 12
    if key == "9":
        waveform_type = "sine" if waveform_type == "saw" else "saw"

    if keyboard_key_to_piano_key_nr(key) != -1:
        piano_key_nr = keyboard_key_to_piano_key_nr(key)

    end_frequency_hz = 440.0 * pow(1.059463,piano_key_nr - 49)
    if kick_mode_active:
        kick_decay = calculate_kick_decay(start_frequency_hz = kick_start_frequency_hz,
                                          end_frequency_hz = end_frequency_hz,
                                          nr_samples = int(44100 * 0.25))

    note_text = urwid.Text(f"Note: {piano_key_nr_to_string(piano_key_nr)}",align="center")
    waveform_text = urwid.Text(f"Waveform: {waveform_type}",align="center")
    octave_down_text = urwid.Text("Z: Octave down",align="left")
    octave_up_text = urwid.Text("X: Octave up",align="left")
    change_waveform_text = urwid.Text("9: Change waveform",align="left")
    exit_text = urwid.Text("Q: Stop audio",align="left")
    pile = urwid.Pile([note_text,waveform_text,octave_down_text,octave_up_text,change_waveform_text,exit_text])
    loop.widget = urwid.Filler(pile)

def kick_mode_activate(loop):
    global kick_mode_active
    global piano_key_nr

    piano_key_nr = 13
    kick_mode_active = True

def kick_mode_deactivate(loop):
    global kick_mode_active

    kick_mode_active = False

root_config_new = {
    "description": "Main Menu",
    "activation_key": "l",
    "children": [
        {
            "activation_key": "0",
            "description": "Play Piano Roll",
            "key_handler": piano_roll_key_handler,
            "activate": piano_roll_activate,
            "deactivate": piano_roll_deactivate
        },
        {
            "activation_key": "9",
            "description": "Activate Kick Mode",
            "action": kick_mode_activate,
        },
        {
            "activation_key": "8",
            "description": "Dectivate Kick Mode",
            "action": kick_mode_deactivate,
        },
    ]
}

def key_handler(key):
    global menu

    if len(key) > 5:
        return # Ignore mouse clicks

    if menu.press_key(key) == True:
        raise urwid.ExitMainLoop()

if __name__ == "__main__":
    placeholder = urwid.SolidFill()
    selector = selectors.SelectSelector()
    async_loop = asyncio.SelectorEventLoop(selector)
    urwid_async_loop = urwid.AsyncioEventLoop(loop=async_loop)
    loop = urwid.MainLoop(placeholder,unhandled_input=key_handler,event_loop=urwid_async_loop)

    menu = interactive_terminal.menu_item_new(root_config_new,None,loop)
    menu.activate()

    loop.run()