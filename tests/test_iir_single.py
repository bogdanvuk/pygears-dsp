import random
import traceback
from scipy import signal
from pygears_dsp.lib.iir import iir_df1dsos, iir_df2tsos
from math import pi, sin
from pygears.lib import check, drv
from pygears.typing import Fixp, Float
from pygears.sim import sim, cosim, log
from pygears import reg

from conftest import set_seed, fixp_sat

############################## SELECT TEST ###############################
test_sel = 0  # 0=iir_df1dsos; 1=iir_df2tsos
enable_svgen = 1  # enables systemVerilog generation
##########################################################################
reg['debug/trace'] = ['*']
reg['debug/webviewer'] = True

# set either random or custom seed
seed = random.randrange(0, 2**32, 1)
# seed = 1379896999

# """Unify all seeds"""
log.info(f'"Random SEED: {seed}')
set_seed(seed)

# set constants
t = list(range(100000))[0:100]
fs = 100000
f1 = 1000
f2 = 70000

# generate inputs
seq = []
for n in t:
    seq.append(1 * sin(2 * pi * f1 / fs * n) + 0.1 * sin(2 * pi * f2 / fs * n))

# generate coefficients
sos = signal.butter(N=5,
                    Wn=30000 / 100000,
                    btype='lowpass',
                    analog=False,
                    output='sos')

# format coefficients
a, b = [], []
for s in sos:
    b.append(list(s[0:3]))
    a.append(list(s[3:]))

coef_type = Fixp[3, 32]
b = [[coef_type(coef) for coef in section] for section in b]
a = [[coef_type(coef) for coef in section] for section in a]

# generate expected outputs
gain = [Fixp[2, 23](1)] * len(b)
ref = signal.sosfilt(sos, seq)

# saturate the results value to filter output type if needed
for i, r in enumerate(ref):
    ref[i] = fixp_sat(Fixp[5, 24], float(r))

# convert ref data to floats
fp_ref = [float(r) for r in ref]
try:
    if test_sel == 0:
        drv(t=Fixp[5, 24], seq=seq) \
        | iir_df1dsos(a=a,b=b, gain=gain, ogain=Fixp[5, 24](1)) \
        | Float \
        | check(ref=fp_ref[:len(seq)], cmp=lambda x, y: abs(x-y) < 1e-3)
        if enable_svgen:
            cosim('iir_df1dsos',
                  'verilator',
                  outdir='../../iir/rtl',
                  timeout=1000)
    else:
        drv(t=Fixp[5, 24], seq=seq) \
        | iir_df2tsos(a=a,b=b, gain=gain, ogain=Fixp[5, 24](1)) \
        | Float \
        | check(ref=fp_ref[:len(seq)], cmp=lambda x, y: abs(x-y) < 1e-3)
        if enable_svgen:
            cosim('iir_df2tsos',
                  'verilator',
                  outdir='../../iir/rtl',
                  timeout=1000)

    sim()
    log.info("\033[92m //==== PASS ====// \033[90m")
except:
    # printing stack trace
    traceback.print_exc()
    log.info("\033[91m //==== FAILED ====// \033[90m")