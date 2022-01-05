import pytest
import numpy as np

from pygears import sim, reg
from pygears.sim import cosim, log
from pygears.lib import drv, collect, flatten
from pygears.typing import Queue, Array, Int

from pygears_dsp.lib.matrix_ops.matrix_multiplication import TCfg, matrix_multiplication
from pygears_dsp.lib.matrix_ops.mult_by_column import column_multiplication
from tests.conftest import set_seed

########################## DESIGN CONTROLS ##########################
num_cols = 4
num_rows = 4  # HINT suported equel dimensions which are power of 2 (4,8,16..)
cols_per_row = 2  # HINT supported even numbers >=2
########################### TEST CONTROLS ###########################
sv_gen = 1
###########################################################################

## input randomization
mat2 = np.random.randint(256, size=(num_cols, 1, num_rows))
mat1 = np.random.randint(256, size=(1, num_cols, num_rows))

print("Inputs: ")
print(type(mat1))
print(mat1)
print(type(mat2))
print(mat2)

reg['trace/level'] = 0
reg['gear/memoize'] = False
reg['trace/debug'] = ['*']
res_list = []

cfg = {
    "cols_per_row": cols_per_row,
    "num_rows": num_rows,
    "num_cols": num_cols,
    'cols_per_multiplier': num_cols // cols_per_row
}
cfg_drv = drv(t=TCfg, seq=[cfg])

row_t = Queue[Array[Int[16], cfg['num_cols']]]
mat1_drv = drv(t=Queue[row_t], seq=[mat1])
mat2_drv = drv(t=Queue[row_t], seq=[mat2])
res = matrix_multiplication(cfg_drv,
                            mat1_drv,
                            mat2_drv,
                            cols_per_row=cols_per_row)
collect(res, result=res_list)

if sv_gen:
    cosim('/matrix_multiplication',
          'verilator',
          outdir='build/matrix_multiplication/rtl',
          rebuild=True,
          timeout=100)
sim('build/matrix_multiplication')

## Print results
pg_res = [int(el) for row_chunk in res_list for el in row_chunk]
pg_res = np.array(pg_res).reshape(num_cols, num_rows)
np_res = np.dot(np.squeeze(mat1),
                np.transpose(mat2.reshape(num_cols, num_rows)))
print("Assert successfully")
assert np.equal(pg_res, np_res).all()
