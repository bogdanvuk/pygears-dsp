import logging
import random
from math import pi, sin

import pytest
from scipy import signal

# from pygears_control.lib import scope
from pygears import reg
from pygears.lib import check, drv
from pygears.sim import log, sim
from pygears.sim.sim import cosim
from pygears.typing import Fixp, Float
from pygears_dsp.lib.iir import iir_df1dsos, iir_df2tsos
from tests.conftest import constant_seq, fixp_sat, random_choice_seq, random_seq, set_seed, sine_seq


def iir_compare(x, y):
    diff = abs(x - y)
    dev = 1e-3
    log.debug(f'{__name__}, exp:{y}, got:{x}')
    log.debug(f'{__name__} deviation:{diff}')
    if (diff > dev):
        log.warning(f'{__name__} deviation error {diff}')
    return diff < dev


def iir_sim(impl,
            t_coef,
            t_in,
            t_out,
            seq,
            target='build/iir',
            do_cosim=False):
    # create SOS referent filter and factors
    sos = signal.butter(N=5,
                        Wn=30000 / 100000,
                        btype='lowpass',
                        analog=False,
                        output='sos')

    # get a,b coefficient from the created filter
    a, b = [], []
    for s in sos:
        b.append(list(s[0:3]))
        a.append(list(s[3:]))

    # convert coefficient to wanted Fixp type
    b = [[t_coef(coef) for coef in section] for section in b]
    a = [[t_coef(coef) for coef in section] for section in a]

    log.info(f'Generated B coeff: {b}')
    log.info(f'Generated A coeff: {a}')

    gain = [t_in(1)] * len(b)
    ref = signal.sosfilt(sos, seq)

    # fp_ref = [float(r) for r in ref]
    # saturate the results value to filter output type if needed
    for i, r in enumerate(ref):
        ref[i] = fixp_sat(t_out, float(r))

    log.info(f'Generated sequence: {seq}')
    log.info(f'Refferenc result: {ref}')
    drv(t=t_in, seq=seq) \
    | impl(a=a, b=b, gain=gain, ogain=t_in(1)) \
    | Float \
    | check(ref=ref[:len(seq)], cmp=iir_compare)

    # optionally generate HDL code do co-simulation in verilator
    if do_cosim:
        cosim(f'{impl}', 'verilator', outdir=target, timeout=1000)

    sim(target, check_activity=False)
    return ref


@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
def test_iir_direct(tmpdir, impl, seed, do_cosim):
    reg['sim/rand_seed'] = seed
    random.seed(reg['sim/rand_seed'])
    log.info(
        f'Running test_fir_direct tmpdir: {tmpdir}, impl: {impl}, seed: {seed}'
    )
    reg['sim/clk_freq'] = 100000
    t = list(range(reg['sim/clk_freq']))[0:100]
    fs = reg['sim/clk_freq']
    f1 = 1000
    f2 = 70000

    seq = []
    for n in t:
        seq.append(1 * sin(2 * pi * f1 / fs * n) +
                   0.1 * sin(2 * pi * f2 / fs * n))

    sos = signal.butter(N=5,
                        Wn=30000 / 100000,
                        btype='lowpass',
                        analog=False,
                        output='sos')

    a, b = [], []
    for s in sos:
        b.append(list(s[0:3]))
        a.append(list(s[3:]))

    t_coef = Fixp[5, 32]

    b = [[t_coef(coef) for coef in section] for section in b]
    a = [[t_coef(coef) for coef in section] for section in a]

    gain = [Fixp[2, 23](1)] * len(b)
    ref = signal.sosfilt(sos, seq)
    fp_ref = [float(r) for r in ref]

    log.info(f'Generated sequence: {seq}')
    drv(t=Fixp[5, 24], seq=seq) \
    | impl(a=a, b=b, gain=gain, ogain=Fixp[5, 24](1)) \
    | Float \
    | check(ref=fp_ref[:len(seq)], cmp=lambda x, y: abs(x - y) < 1e-3)

    if do_cosim:
        cosim(f'{impl}', 'verilator', outdir=tmpdir, timeout=1000)

    sim(tmpdir, check_activity=False)


@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
def test_iir_random(impl, seed, do_cosim):
    log.info(f'Running test_iir_random seed: {seed}')
    set_seed(seed)

    ftype = Fixp[5, 32]

    seq = constant_seq(ftype, 10, 0)
    seq.extend(random_seq(ftype, 100))
    seq.extend(constant_seq(ftype, 10, 0))

    iir_sim(impl, ftype, ftype, ftype, seq, do_cosim=do_cosim)


@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
def test_iir_random_type(impl, seed, do_cosim):
    log.info(f'Running test_iir_random, seed: {seed}')
    set_seed(seed)

    # minimum supported precision Fixp[3,19]
    int_w = random.randint(3, 7)
    fixp_w = random.randint(int_w + 19, int_w + 32)
    ftype = Fixp[int_w, fixp_w]

    log.info(
        f'{__name__} FIR input type t_b: {ftype} min: {ftype.fmin}, max: {ftype.fmax}'
    )

    seq = constant_seq(ftype, 10, 0)
    seq.extend(random_seq(ftype, 100))
    seq.extend(constant_seq(ftype, 10, 0))

    iir_sim(impl, ftype, ftype, ftype, seq, do_cosim=do_cosim)


# HINT -> IIR implementation errors when testing extreme inputs
# errors are due to different precision used than reference results
@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
@pytest.mark.parametrize('fixp_w', range(25, 33, 4))
@pytest.mark.parametrize('int_w', range(3, 7))
def test_iir_limits(fixp_w, int_w, impl, seed, do_cosim):
    """[Drive filter with extreme values [min, 0 , max]
    """
    log.info(f'Running test_iir_limits, seed: {seed}')
    set_seed(seed)
    factor = 0.5  # supported factor

    ftype = Fixp[int_w, fixp_w]
    print(f'max possible value {ftype.fmax}')
    extremes = [[0 for i in range(50)]]
    extremes.append([ftype.fmin * factor for i in range(10)])
    seq = random_choice_seq(extremes, 10)
    extremes.append([ftype.fmax * factor for i in range(10)])
    seq = random_choice_seq(extremes, 10)
    iir_sim(impl, ftype, ftype, ftype, seq, do_cosim=do_cosim)


@pytest.mark.parametrize('impl', [iir_df1dsos, iir_df2tsos])
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
    log.info(f'Running {__name__} impl: {impl}, seed: {seed}, fs:{fs},f1:{f1}')

    ftype = Fixp[5, 32]
    seq = [0 for i in range(10)]
    seq.extend(sine_seq(f1, fs, 200, ftype))
    seq.extend([0 for i in range(100)])
    seq.extend(sine_seq(f1, fs / 2, 100, ftype))
    seq.extend([0 for i in range(100)])
    seq.extend(sine_seq(f1, fs * 2, 400, ftype))
    seq.extend([0 for i in range(10)])
    res = iir_sim(impl, ftype, ftype, ftype, seq, do_cosim=do_cosim)


# reg['logger/sim/error'] = 'debug'  # on error open cmdline debugger
# reg['logger/sim/error'] = 'continue'  # on error continue
# reg['logger/sim/level'] = logging.DEBUG
reg['debug/trace'] = ['*']
reg['debug/webviewer'] = True

## HINT : for debugging individual tests
# test_iir_direct('build', iir_df2tsos, 2,do_cosim=False)
# test_iir_random(iir_df2tsos, 1,do_cosim=False)
# test_iir_random_type(iir_df2tsos, 1,do_cosim=False)
test_iir_limits(46, 3, iir_df2tsos, 1, do_cosim=False)
# test_fir_sine(100_000,iir_df2tsos, 12,do_cosim=False)
