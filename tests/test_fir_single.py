import traceback
from os.path import abspath
import random

import numpy as np
from scipy.signal import firwin

from pygears import reg
from pygears.lib import check, drv
from pygears.sim import cosim, log, sim
from pygears.typing import Fixp, Float
from pygears_dsp.lib.fir import fir_direct, fir_transposed
from conftest import fixp_sat, set_seed

############################## SELECT TEST ###############################
test_sel = 1  # 0=fir_direct; 1=fir_transposed
enable_svgen = 0  # enables systemVerilog generation
##########################################################################
# >> used to probe all signals
reg['debug/trace'] = ['*']
# >> used to enable JSON file creation for webviewer support
reg['debug/webviewer'] = True

# set either random or custom seed
seed = random.randrange(0, 2**32, 1)
# seed = 1379896999

# """Unify all seeds"""
log.info(f"Random SEED: {seed}")
set_seed(seed)

# generate b coefficients
b_coef = firwin(8, [0.05, 0.95], width=0.05, pass_zero=False)

# generate quantized b coefficients
b_coef_type = Fixp[1, 15]
b_coef_fixp = [b_coef_type(i) for i in b_coef]

# generate random inputs
x = np.random.random(size=(10, ))

# calculated expected outputs
ref = np.convolve(x, b_coef)

# saturate the results value to filter output type if needed
for i, r in enumerate(ref):
    ref[i] = fixp_sat(b_coef_type, float(r))

try:
    if test_sel == 0:
        drv(t=b_coef_type, seq=x) \
        | fir_direct(b=b_coef_fixp) \
        | Float \
        | check(ref=ref[:len(x)], cmp=lambda x, y: abs(x-y) < 1e-3)

        if enable_svgen:
            cosim('fir_direct',
                  'verilator',
                  outdir='../../outputs/fir/rtl',
                  timeout=1000)
    else:
        drv(t=b_coef_type, seq=x) \
        | fir_transposed(b=b_coef_fixp) \
        | Float \
        | check(ref=ref[:len(x)], cmp=lambda x, y: abs(x-y) < 1e-3)

        if enable_svgen:
            cosim('fir_transposed',
                  'verilator',
                  outdir='../../outputs/fir/rtl',
                  timeout=1000)

    sim()
    log.info("\033[92m //==== PASS ====// \033[90m")
except:
    # printing stack trace
    traceback.print_exc()
    log.info("\033[91m //==== FAILED ====// \033[90m")