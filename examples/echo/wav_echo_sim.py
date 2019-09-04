import wav_utils

from pygears_dsp.lib.echo import echo
from pygears import gear
from pygears.sim import sim
from pygears.lib import drv
from pygears.sim.modules import SimVerilated
from pygears.typing import Fixp, Tuple, typeof


def wav_echo_sim(ifn,
                 ofn,
                 stereo=True,
                 cosim=True,
                 sample_rng=None,
                 feedback_gain=0.6,
                 delay=0.25):
    """Applies echo effect on a WAV file using Verilator cosimulation

    ifn - Input WAV file name
    ofn - Output WAV file name
    """

    samples_all, params = wav_utils.load_wav(ifn, stereo=stereo)
    samples = samples_all[:sample_rng]

    sample_bit_width = 8 * params.sampwidth
    sample_type = Fixp[1, sample_bit_width]

    if stereo:
        stream_type = Tuple[sample_type, sample_type]

        def decode_sample(seq):
            for s in seq:
                yield stream_type(
                    (sample_type.decode(s[0]), sample_type.decode(s[1])))
    else:
        stream_type = sample_type

        def decode_sample(seq):
            for s in seq:
                yield sample_type.decode(s)

    result = []
    drv(t=stream_type, seq=decode_sample(samples)) \
        | echo(feedback_gain=feedback_gain,
               sample_rate=params.framerate,
               delay=delay,
               sim_cls=SimVerilated if cosim else None) \
        | collect(result=result, samples_num=len(samples))

    # sim(outdir='./build', extens=[Profiler])
    sim(outdir='./build')

    wav_utils.dump_wav(ofn, result, params, stereo=stereo)

    try:
        wav_utils.plot_wavs(samples, result, stereo=stereo)
    except:
        pass


@gear
async def collect(din, *, result, samples_num):
    async with din as val:
        if len(result) % 10 == 0:
            if samples_num is not None:
                print(f"Calculated {len(result)}/{samples_num} samples",
                      end='\r')
            else:
                print(f"Calculated {len(result)} samples", end='\r')

        if typeof(din.dtype, Tuple):
            result.append((int(val[0]), int(val[1])))
        else:
            result.append(int(val))
