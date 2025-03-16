#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "ffmpeg-python",
#   "ffpb",
#   "tqdm",
# ]
# ///

import ffmpeg, ffpb, tqdm

import optparse, sys, shlex, os
from functools import partial
from subprocess import Popen, PIPE

parser = optparse.OptionParser()
parser.add_option('-s', '--size', dest='target_video_size_MB', default=4000, help='target_video_size in MB')
parser.add_option('-e', '--ext', dest='files_ext', default='', help='convert all files with this ext (mp4 4ex)')
options, arguments = parser.parse_args()

def probe(file_path):
    probe = ffmpeg.probe(file_path)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    audio_bitrate = float(audio_stream['bit_rate'] if audio_stream and 'bit_rate' in audio_stream else None) / 1000
    duration = float(probe['format']['duration'])
    return duration, audio_bitrate 

def conv(filename):
    print(filename)
    name, extension = os.path.splitext(filename)
    duration, audio_bitrate = probe(filename)
    print(f"duration = {duration}, audio_bitrate = {audio_bitrate}")
    
    target_audio_bitrate = audio_bitrate # TODO: Adjust target audio bitrate. Use source bitrate for now
    target_video_bitrate = int(options.target_video_size_MB) * 8192 / (1.048576 * duration) - target_audio_bitrate
    print(f"target_audio_bitrate = {target_audio_bitrate}, target_video_bitrate = {target_video_bitrate}")

    first_cmd  = f'-y -i \"{filename}\" -c:v h264_nvenc -b:v {target_video_bitrate}k -pass 1 -an -f mp4 nul'
    second_cmd = f'-y -i \"{filename}\" -c:v h264_nvenc -b:v {target_video_bitrate}k -pass 2 -c:a aac -b:a {target_audio_bitrate}k \"{name} {options.target_video_size_MB}MB{extension}\"'
    ffpb.main(argv=shlex.split(first_cmd))
    ffpb.main(argv=shlex.split(second_cmd))
    print()
	
print(f"target_video_size_MB => {options.target_video_size_MB}")

if options.files_ext:
    arguments = [f for f in os.listdir('.') if f.endswith(options.files_ext)]

for arg in arguments:
	conv(arg)
