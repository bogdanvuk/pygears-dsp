import pytest
import numpy as np

from pygears import sim, reg
from pygears.sim import cosim, log
from pygears.lib import drv, collect, flatten
from pygears.typing import Queue, Array, Int

from pygears_dsp.lib.matrix_ops.matrix_multiplication import TCfg, matrix_multiplication
from pygears_dsp.lib.matrix_ops.mult_by_column import column_multiplication
from tests.conftest import set_seed

mat2 = np.random.randint(256, size=(8, 1, 8))
mat1 = np.random.randint(256, size=(1, 8, 8))


def create_valid_cfg(cols_per_row, mat1):
    num_rows, num_cols = np.squeeze(mat1).shape
    cfg = {
        "cols_per_row": cols_per_row,
        "num_rows": num_rows,
        "num_cols": num_cols,
        'cols_per_multiplier': num_cols // cols_per_row
    }
    return cfg


@pytest.mark.parametrize('mat1', [mat1])
@pytest.mark.parametrize('mat2', [mat2])
@pytest.mark.parametrize('cols_per_row', [2, 4])
@pytest.mark.parametrize('impl', ['high', 'hw'])
def test_matrix_mult(impl, mat1, mat2, cols_per_row, seed):
    set_seed(seed)
    reg['trace/level'] = 0
    reg['gear/memoize'] = False
    # reg['trace/debug'] = ['*']
    res_list = []

    cfg = create_valid_cfg(cols_per_row, mat1)
    cfg_drv = drv(t=TCfg, seq=[cfg])

    row_t = Queue[Array[Int[16], cfg['num_cols']]]
    mat1_drv = drv(t=Queue[row_t], seq=[mat1])
    mat2_drv = drv(t=Queue[row_t], seq=[mat2])
    res = matrix_multiplication(cfg_drv,
                                mat1_drv,
                                mat2_drv,
                                cols_per_row=cols_per_row)
    collect(res, result=res_list)
    if impl == 'hw':
        cosim('/matrix_multiplication',
              'verilator',
              outdir='/tmp/matrix_multiplication',
              rebuild=True,
              timeout=100)
    sim()
    pg_res = [int(el) for row_chunk in res_list for el in row_chunk]
    pg_res = np.array(pg_res).reshape(8, 8)
    np_res = np.dot(np.squeeze(mat1), np.transpose(mat2.reshape(8, 8)))
    print("Assert successfully")
    assert np.equal(pg_res, np_res).all()


@pytest.mark.parametrize('mat1', [mat1])
@pytest.mark.parametrize('mat2', [mat2])
@pytest.mark.parametrize('cols_per_row', [1])
@pytest.mark.parametrize('impl', ['high', 'hw'])
def test_column_multiplicator(impl, mat1, mat2, cols_per_row, seed):
    set_seed(seed)
    reg['trace/level'] = 0
    res_list = []
    mat2 = np.squeeze(mat2)
    cfg = create_valid_cfg(cols_per_row, mat1)
    cfg_drv = drv(t=TCfg, seq=[cfg])

    row_t = Queue[Array[Int[16], cfg['num_cols']]]
    mat1_drv = drv(t=Queue[row_t], seq=[mat1])
    mat2_drv = drv(t=row_t, seq=[mat2])
    res = column_multiplication(cfg_drv, mat1_drv, mat2_drv)
    collect(res | flatten, result=res_list)
    if impl == 'hw':
        cosim('/column_multiplication',
              'verilator',
              outdir='/tmp/column_multiplication',
              rebuild=True,
              timeout=100)
    sim()
    pg_res = [int(el) for el in res_list]
    pg_res = np.array(pg_res).reshape(8, 8)
    np_res = np.dot(np.squeeze(mat1), np.transpose(np.squeeze(mat2)))
    assert np.equal(pg_res, np_res).all()
    # print("Success,", {pg_res})
    log.info(f"log message {pg_res} {np_res}")
    log.warning(f"log message {pg_res} {np_res}")
