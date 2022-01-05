import logging
import random

import numpy as np
import pytest
from scipy.signal.fir_filter_design import firwin

from pygears import reg
from pygears.lib import check, drv
from pygears.sim import log, sim
from pygears.sim.sim import cosim
from pygears.typing import Fixp, Float
from pygears_dsp.lib.fir import fir_direct, fir_transposed
from tests.conftest import fixp_sat, random_choice_seq, random_seq, set_seed, sine_seq


def fir_compare(x, y):
    diff = abs(x - y)
    dev = 1e-3
    log.debug(f'fir_compare Result exp: {y},  got: {x}')
    log.debug(f'fir_compare Result deviation {diff}')
    if (diff > dev):
        log.warning(f'fir_compare Result deviation error {diff}')
    return diff < dev


def fir_sim(impl, t_b, seq, do_cosim, target='build/fir'):
    # get 'b' factors
    b = firwin(8, [0.05, 0.95], width=0.05, pass_zero=False)
    b_fixp = [t_b(i) for i in b]

    # get result
    res = np.convolve(seq, b)

    # saturate the results value to filter output type if needed
    for i, r in enumerate(res):
        res[i] = fixp_sat(t_b, r)

    # driving
    drv(t=t_b, seq=seq) \
        | impl(b=b_fixp) \
        | Float \
        | check(ref=res[:len(seq)], cmp=fir_compare)

    # optionally generate HDL code do co-simulation in verilator
    if do_cosim:
        cosim(f'{impl}', 'verilator', outdir=target, timeout=1000)

    # simulation start
    sim(target, check_activity=False)
    return res


@pytest.mark.parametrize('impl', [fir_direct, fir_transposed])
def test_fir_random(impl, seed, do_cosim):
    # Set random seed
    set_seed(seed)

    log.info(f'Running {__name__} impl: {impl}, seed: {seed}')

    t_b = Fixp[1, 15]

    # genrate  random numbers in [-1,1)
    seq = np.random.random(size=(100, )) * 2 - 1
    log.debug(f'Generated sequence: {seq}')

    res = fir_sim(impl, t_b, seq, do_cosim=do_cosim)


@pytest.mark.parametrize('impl', [fir_direct, fir_transposed])
def test_fir_random_type(impl, seed, do_cosim):
    # Set random seed
    set_seed(seed)

    log.info(f'{__name__} impl: {impl}, seed: {seed}')

    fixp_w = random.randint(16, 32)
    int_w = random.randint(1, 3)

    t_b = Fixp[int_w, fixp_w]
    log.info(
        f'{__name__} FIR input type t_b: {t_b} min: {t_b.fmin}, max: {t_b.fmax}'
    )

    seq = []
    # generate multiple constant sequences of certain size
    for i in range(10):
        num = np.random.uniform(t_b.fmin, t_b.fmax)
        for i in range(50):
            seq.append(num)
    # add a random sequence of certain size
    seq.extend(random_seq(t_b, 100))

    # genrate  random numbers in [-1,1)
    # seq = np.random.random(size=(100, )) * 2 - 1
    log.debug(f'Generated sequence: {seq}')

    res = fir_sim(impl, t_b, seq, do_cosim=do_cosim)


@pytest.mark.parametrize('impl', [fir_direct, fir_transposed])
@pytest.mark.parametrize('fixp_w', range(16, 33, 4))
@pytest.mark.parametrize('int_w', range(1, 3))
def test_fir_limits(fixp_w, int_w, impl, seed, do_cosim):
    """[Drive filter with extreme values [min, 0 , max]
    """
    # Set random seed
    set_seed(seed)

    log.info(f'Running {__name__} impl: {impl}, seed: {seed}')

    t_b = Fixp[int_w, fixp_w]
    log.info(
        f'{__name__} FIR input type t_b: {t_b} min: {t_b.fmin}, max: {t_b.fmax}'
    )

    extremes = [[0 for i in range(50)]]
    extremes.append([t_b.fmin for i in range(50)])
    extremes.append([t_b.fmax for i in range(50)])
    seq = random_choice_seq(extremes, 10)

    log.debug(f'Generated sequence: {seq}')

    res = fir_sim(impl, t_b, seq, do_cosim=do_cosim)


@pytest.mark.parametrize('impl', [fir_direct, fir_transposed])
@pytest.mark.parametrize('freq', [10_000, 100_000, 1_000_000])
def test_fir_sine(freq, impl, seed, do_cosim):
    """[Drive filter with sine signal at fs fs/2 and fs*2 
    """
    # Set random seed
    set_seed(seed)
    # set clock freq
    reg['sim/clk_freq'] = freq
    t = list(range(reg['sim/clk_freq']))[0:100]
    fs = reg['sim/clk_freq']
    f1 = freq / 100

    log.info(f'Running {__name__} impl: {impl}, seed: {seed}')

    t_b = Fixp[1, 15]
    seq = [0 for i in range(10)]
    seq.extend(sine_seq(f1, fs, 200, t_b))
    seq.extend(sine_seq(f1, fs / 2, 100, t_b))
    seq.extend(sine_seq(f1, fs * 2, 400, t_b))
    seq.extend([0 for i in range(10)])

    log.debug(f'Generated sequence: {seq}')

    res = fir_sim(impl, t_b, seq, do_cosim=do_cosim)


## >> used to probe all signals
# reg['debug/trace'] = ['*']

## >> used to enable JSON file creation for webviewer support
# reg['debug/webviewer'] = True

## >> used to break to debugger on error
# reg['logger/sim/error'] = 'debug'  # on error open cmdline debugger

## >> used to continue the simulation on errors
# reg['logger/sim/error'] = 'continue'  # on error continue

## >> used to print additional debug messages
# reg['logger/sim/level'] = logging.DEBUG

## HINT : for debugging individual tests
# test_fir_random(fir_direct, 12, do_cosim=True)
# test_fir_limits(fir_transposed, 1, do_cosim=True)
# test_fir_sine(1_000_000,fir_direct, 12, do_cosim=True)
