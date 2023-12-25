from pydub import AudioSegment
from pydub.playback import play

kempis_file = "/home/jetson/PIMNAS/Kempes.mp3"
suhu_file = "/home/jetson/PIMNAS/suhu.mp3"
alarm_file = "/home/jetson/PIMNAS/alarm.mp3"

def play_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    play(audio)



