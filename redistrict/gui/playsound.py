# pylint: skip-file


def _playsoundWin(sound, block=True):
    from winsound import PlaySound, SND_ASYNC, SND_FILENAME

    PlaySound(sound, SND_FILENAME | (0 if block else SND_ASYNC))


def _playsoundOSX(sound, block=True):
    from AppKit import NSSound
    from time import sleep

    sound = NSSound.alloc().initWithContentsOfFile_byReference_(sound, True)
    sound.play()

    if block:
        sleep(sound.duration())


def _playsoundNix(sound, block=True):
    import ossaudiodev
    from sys import byteorder
    from wave import open as waveOpen

    with waveOpen(sound, 'rb') as sound:
        channelCount, sampleWidth, framerate, frameCount, compressionType, compressionName = sound.getparams()
        try:
            from ossaudiodev import AFMT_S16_NE
        except ImportError:
            if 'little' in byteorder.lower():
                AFMT_S16_NE = ossaudiodev.AFMT_S16_LE
            else:
                AFMT_S16_NE = ossaudiodev.AFMT_S16_BE
        data = sound.readframes(frameCount)

    speaker = ossaudiodev.open('/dev/dsp', 'w')
    speaker.setparameters(AFMT_S16_NE, channelCount, framerate)
    speaker.write(data)
    speaker.close()


from platform import system

system = system()

if system == 'Windows':
    playsound = _playsoundWin
elif system == 'Darwin':
    playsound = _playsoundOSX
else:
    playsound = _playsoundNix

del system
