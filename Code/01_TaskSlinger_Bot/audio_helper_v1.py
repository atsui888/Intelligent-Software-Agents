import io
import subprocess


def mp3_to_ogg(filename, path=''):
    with open(f'{path}{filename}.mp3', 'rb') as input_file:
        mp3_io = io.BytesIO(input_file.read())
        ffmpeg_command = ['ffmpeg', '-i', 'pipe:0', '-c:a', 'libopus', '-f', 'ogg', 'pipe:1']
        result = subprocess.run(ffmpeg_command, input=mp3_io.read(), capture_output=True)
        return result.stdout  # bytes
