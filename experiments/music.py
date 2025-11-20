from just_playback import Playback
import time

playback = Playback()
playback.load_file("/Users/seangaffney/Music/tunes/Let's Begin [ne7d4T3LQMU].mp3")
playback.play()

# playback2 = Playback()
# playback2.load_file("/Users/seangaffney/Music/tunes/Go Mode [DxumXOxEoxM].mp3")
# playback2.play()

volume = 0.5
volume2 = 0

playback.set_volume(volume)
# playback2.set_volume(volume2)

increase = False

# print(playback.duration)
while playback.active:
    # print(playback.curr_pos)

    if increase:
        volume += 0.01
    else:
        volume -= 0.01

    # print(f"Volume1: {playback.volume}, Volume2: {playback2.volume}")

    time.sleep(0.1)