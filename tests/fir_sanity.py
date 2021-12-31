from os.path import abspath

import numpy as np
from scipy.signal import firwin

from pygears.lib import check, drv
from pygears.sim import cosim, sim
from pygears.typing import Fixp, Float
from pygears_dsp.lib.fir import fir_direct, fir_transposed

############################## SELECT TEST ###############################
test_sel = 1  # 0=fir_direct; 1=fir_transposed
enable_svgen = 0  # enables systemVerilog generation
##########################################################################

    
# generate b coefficients
b_coef = firwin(8, [0.05, 0.95], width=0.05, pass_zero=False)

# generate quantized b coefficients
b_coef_type = Fixp[1, 15]
b_coef_fixp = [b_coef_type(i) for i in b_coef]

# generate random inputs
x = np.random.random(size=(10, ))

# calculated expected outputs
res = np.convolve(x, b_coef)

if test_sel == 0:
    drv(t=b_coef_type, seq=x) \
    | fir_direct(b=b_coef_fixp) \
    | Float \
    | check(ref=res[:len(x)], cmp=lambda x, y: abs(x-y) < 1e-3)

    if enable_svgen:
        cosim('fir_direct', 'verilator', outdir='../../outputs/fir/rtl', timeout=1000)
else:
    drv(t=b_coef_type, seq=x) \
    | fir_transposed(b=b_coef_fixp) \
    | Float \
    | check(ref=res[:len(x)], cmp=lambda x, y: abs(x-y) < 1e-3)

    if enable_svgen:
        cosim('fir_transposed', 'verilator', outdir='../../outputs/fir/rtl', timeout=1000)

sim()
