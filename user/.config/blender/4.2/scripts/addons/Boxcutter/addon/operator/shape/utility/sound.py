
import os

import bpy
# import aud

from ..... utility import addon, screen, view3d


def play(name):
    volume = addon.preference().display.sound_volume

    if not load(name) or not volume:
        return

    sound = aud.Sound(load(name))
    device = aud.Device()

    device.volume = volume / 100
    device.play(sound)


def load(name):
    sound = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sound', name)
    extension = F'.{name.split(".")[-1]}'

    if extension not in bpy.path.extensions_audio:
        print(F'Unable to play audio with this blender build: {type}')
        return None

    return sound
