import aud

device = aud.Device()
# load sound file (it can be a video file with audio)
sound = aud.Sound('music.ogg')

# play the audio, this return a handle to control play/pause
handle = device.play(sound)
# if the audio is not too big and will be used often you can buffer it
sound_buffered = aud.Sound.cache(sound)
handle_buffered = device.play(sound_buffered)

# stop the sounds (otherwise they play until their ends)
handle.stop()
handle_buffered.stop()

#####
# import os

# import bpy
# import aud

# from ..... utility import addon, screen, view3d


# def play(name):
#     volume = addon.preference().display.sound_volume

#     if not load(name) or not volume:
#         return

#     sound = aud.Sound(load(name))
#     device = aud.Device()

#     device.volume = volume / 100
#     device.play(sound)


# def load(name):
#     sound = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sound', name)
#     extension = F'.{name.split(".")[-1]}'

#     if extension not in bpy.path.extensions_audio:
#         print(F'Unable to play audio with this blender build: {type}')
#         return None

#     return sound
