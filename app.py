#!/usr/bin/env python3

import asyncio
import interactive_terminal
import pyaudio
import selectors
import urwid

def beep_callback(in_data,frame_count,time_info,status):
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

continue_playing_audio = False
nr_audio_callbacks_run = 0
pa = pyaudio.PyAudio()
stream = pa.open(format=pa.get_format_from_width(2,True),
                 channels=2,
                 rate=44100,
                 output=True,
                 stream_callback=beep_callback)
stream.stop_stream()

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

root_config_new = {
    "description": "Main Menu",
    "activation_key": "l",
    "children": [
        {
            "activation_key": "a",
            "description": "Menu A",
            "children": [
                {
                    "activation_key": "o",
                    "description": "Make a noise once",
                    "action": play_once
                },
                {
                    "activation_key": "c",
                    "description": "Make a noise continuously",
                    "action": play_continuously
                },
                {
                    "activation_key": "s",
                    "description": "Stop the noise",
                    "action": stop_playing
                }
            ]
        },
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