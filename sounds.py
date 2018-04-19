from pygame import mixer

mixer.init()

def play_sound(soundfile):
    mixer.music.load(open(soundfile))
    mixer.music.play()