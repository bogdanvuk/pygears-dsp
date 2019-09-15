import pytest
from pygears_dsp.lib.fir import fir_direct, fir_transposed
from pygears.lib import drv, collect, check
from scipy.signal import firwin
from pygears.typing import Fixp, Float
from pygears.sim import sim
import numpy as np


@pytest.mark.parametrize('impl', [fir_direct, fir_transposed])
def test_fir_direct(tmpdir, impl):
    b = firwin(8, [0.05, 0.95], width=0.05, pass_zero=False)

    t_b = Fixp[1, 15]
    b_fixp = [t_b(i) for i in b]

    x = np.random.random(size=(10, ))
    res = np.convolve(x, b)

    drv(t=t_b, seq=x) \
        | impl(b=b_fixp) \
        | Float \
        | check(ref=res[:len(x)], cmp=lambda x, y: abs(x-y) < 1e-3)

    sim(tmpdir, check_activity=False)
