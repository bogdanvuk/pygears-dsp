from pygears import gear, Intf, alternative
from pygears.lib import decouple, tuplemap, union_collapse, trunc
from pygears.typing import Fixp, ceil_pow2, Tuple
from pygears.lib import flatten, priority_mux, replicate, once


@gear
def prefill(din, *, num, dtype):
    fill = once(val=dtype(0)) \
        | replicate(num) \
        | flatten

    return priority_mux(fill, din) \
        | union_collapse


@gear
def echo(din: Fixp, *, feedback_gain, sample_rate, delay):
    """Performs echo audio effect on the continuous input sample stream

    Args:
        din: Stream of audio samples

    Keyword Args:
        feedback_gain (float): gain of the feedback loop
        sample_rate (int): samples per second
        delay (float): delay in seconds
        precision (int): sample fixed point precision
        sample_width (int): sample width in bits

    Returns:
        - **dout** - Stream of audio samples with applied echo

    """

    #########################
    # Parameter calculation #
    #########################

    sample_dly_len = round(sample_rate * delay)
    fifo_depth = ceil_pow2(sample_dly_len)
    feedback_gain_fixp = din.dtype(feedback_gain)

    #########################
    # Hardware description  #
    #########################

    dout = Intf(din.dtype)

    feedback = dout \
        | decouple(depth=fifo_depth) \
        | prefill(dtype=din.dtype, num=sample_dly_len)

    feedback_attenuated = trunc(feedback * feedback_gain_fixp, t=din.dtype)

    dout |= trunc(din + feedback_attenuated, t=dout.dtype)

    return dout


@alternative(echo)
@gear
def stereo_echo(
        din: Tuple[Fixp, Fixp],  # audio samples
        *,
        feedback_gain,  # feedback gain == echo gain
        sample_rate,  # sample_rate in samples per second
        delay  # delay in seconds
):

    mono_echo = echo(feedback_gain=feedback_gain,
                     sample_rate=sample_rate,
                     delay=delay)

    return din | tuplemap(f=(mono_echo, mono_echo))
