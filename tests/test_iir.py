from scipy import signal
import numpy as np
from pygears_dsp.lib.iir import iir_direct1_sos
from pygears.lib import drv, shred, collect
from pygears.typing import Fixp, Float
from pygears.sim import sim
from pygears_control.lib import lti, scope
from pygears import config

from math import sin, cos, pi

b, a = signal.iirfilter(1, [2 * np.pi * 50, 2 * np.pi * 200],
                        rs=60,
                        btype='band',
                        analog=True,
                        ftype='cheby2')

config['sim/clk_freq'] = 100000
t = list(range(config['sim/clk_freq']))[0:100]
fs = config['sim/clk_freq']
f1 = 1000
f2 = 70000

seq = []
for n in t:
    seq.append(10 * sin(2 * pi * f1 / fs * n) + 1 * sin(2 * pi * f2 / fs * n))

b = [
    0.211939524148286456695089441382151562721,
    0.471832709834875574372858864080626517534,
    0.471832709834875574372858864080626517534,
    0.211939524148286456695089441382151562721
]

b_fixp = [Fixp[1, 23](i) for i in b]

din = drv(t=Fixp[5, 24], seq=seq)
dout = din | iir_direct1_sos(a=b_fixp, b=b_fixp, gain=Fixp[1, 23](0.123123))
# dout | Float | scope
result = []
dout | collect(result=result)

ref = signal.lfilter(b, b, seq)

sim('/tools/home/tmp/vcd_test', timeout=len(seq), check_activity=False)
sim(timeout=len(seq), check_activity=False)

fp_res = [float(r) for r in result]

diff = [abs(a-b) for a, b in zip(ref, fp_res)]
print(diff)
