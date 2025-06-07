#!/usr/bin/env python3

import asyncio
import interactive_terminal
import pyaudio
import selectors
import urwid

def play_callback(in_data,frame_count,time_info,status):
    global nr_audio_callbacks_run
    global stop_audio_loopback

    sample = -1.0
    data = list()
    if nr_audio_callbacks_run > 50:
        if stop_audio_loopback:
            return (b'x00',pyaudio.paAbort) # End audio stream.
        else:
            nr_audio_callbacks_run = 0
    for frame_index in range(frame_count * 2):
        sample_word = int((sample + 1.0) / 2.0 * 65535)
        data.append(int(sample_word / 255) % 255)
        data.append(int(sample_word % 255))
        next_sample = sample + 0.1 / (nr_audio_callbacks_run + 1)
        sample = next_sample if next_sample < 1.0 else -1.0
    nr_audio_callbacks_run += 1
    return (bytes(data),pyaudio.paContinue)

# Globals
continue_playing_audio = False
nr_audio_callbacks_run = 0
pa = pyaudio.PyAudio()
stream = pa.open(format=pa.get_format_from_width(2,True),
                 channels=2,
                 rate=44100,
                 output=True,
                 stream_callback=play_callback)
stream.stop_stream()
octave = 1
piano_key_nr = 0

async def stream_audio():
    global stop_audio_loopback
    global stream

    while stream.is_active():
        await asyncio.sleep(0)

    stream.start_stream()

    while stream.is_active():
        await asyncio.sleep(0)
    
    if stop_audio_loopback:
        stream.stop_stream()

def play_once(loop):
    global nr_audio_callbacks_run
    global stop_audio_loopback

    nr_audio_callbacks_run = 0
    stop_audio_loopback = True

    asyncio.create_task(stream_audio())

def play_continuously(loop):
    global nr_audio_callbacks_run
    global stop_audio_loopback
    
    nr_audio_callbacks_run = 0
    stop_audio_loopback = False

    asyncio.create_task(stream_audio())

def stop_playing(loop):
    global stop_audio_loopback
    global stream

    stop_audio_loopback = True
    stream.stop_stream()

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
    }

    if key.upper() not in note_index_from_keyboard_keys:
        return -1 # Something else can handle this key.

    note_index = note_index_from_keyboard_keys[key.upper()]
    note_index_root_c = octave * 12 - 8
    return note_index_root_c + note_index

def piano_roll_key_handler(loop,key):
    global piano_key_nr
    global octave
    
    if keyboard_key_to_piano_key_nr(key) != -1:
        piano_key_nr = keyboard_key_to_piano_key_nr(key)

    if key.upper() == "Z" and octave > 1:
        octave -= 1
    if key.upper() == "X" and octave < 6:
        octave += 1

    note_text = urwid.Text(piano_key_nr_to_string(piano_key_nr),align="center")
    loop.widget = urwid.Filler(note_text)

root_config_new = {
    "description": "Main Menu",
    "activation_key": "l",
    "children": [
        {
            "activation_key": "a",
            "description": "Play Loop / Oneshot",
            "children": [
                {
                    "activation_key": "o",
                    "description": "Make sound once",
                    "action": play_once
                },
                {
                    "activation_key": "c",
                    "description": "Make sound continuously",
                    "action": play_continuously
                },
                {
                    "activation_key": "s",
                    "description": "Stop the sound",
                    "action": stop_playing
                }
            ]
        },
        {
            "activation_key": "0",
            "description": "Play Piano Roll",
            "key_handler": piano_roll_key_handler
        }
    ]
}

def key_handler(key):
    global menu
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