import os
from os import sys

from wav_echo_sim import wav_echo_sim

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
if len(sys.argv) > 1 and type(sys.argv[1]) is str:
    sound_name = sys.argv[1]
else:
    sound_name = 'plop.wav'

if len(sys.argv) > 2 and type(sys.argv[2]) is str:
    out_name = sys.argv[2]
else:
    out_name = 'plop_echo.wav'
print(f'Running with sound  file: {sound_name}')

wav_echo_sim(os.path.join(os.path.dirname(__file__), sound_name),
             os.path.join('build', out_name),
             feedback_gain=0.6,
             delay=0.25,
             stereo=False)
