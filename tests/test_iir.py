from scipy import signal
from pygears_dsp.lib.iir import iir_df1dsos, iir_df2tsos
from pygears.sim import sim
from pygears_control.lib import scope
from pygears import config
from math import pi, sin
import pytest
from pygears.lib import check, drv
from pygears.typing import Fixp, Float
from pygears.sim import sim


@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
def test_iir_direct(tmpdir, impl):
    config['sim/clk_freq'] = 100000
    t = list(range(config['sim/clk_freq']))[0:100]
    fs = config['sim/clk_freq']
    f1 = 1000
    f2 = 70000

    seq = []
    for n in t:
        seq.append(1 * sin(2 * pi * f1 / fs * n) +
                   0.1 * sin(2 * pi * f2 / fs * n))

    sos = signal.butter(
        N=5, Wn=30000 / 100000, btype='lowpass', analog=False, output='sos')

    a, b = [], []
    for s in sos:
        b.append(list(s[0:3]))
        a.append(list(s[3:]))

    t_coef = Fixp[2, 32]

    b = [[t_coef(coef) for coef in section] for section in b]
    a = [[t_coef(coef) for coef in section] for section in a]

    gain = [Fixp[1, 23](1)] * len(b)
    ref = signal.sosfilt(sos, seq)
    fp_ref = [float(r) for r in ref]

    drv(t=Fixp[5, 24], seq=seq) \
        | impl(a=a,b=b, gain=gain, ogain=1) \
        | Float \
        | check(ref=fp_ref[:len(seq)], cmp=lambda x, y: abs(x-y) < 1e-3)

    sim(tmpdir, check_activity=False)


# test_iir_direct('build', impl=iir_df1dsos)
