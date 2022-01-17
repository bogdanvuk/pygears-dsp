import traceback

import numpy as np
import pytest

from pygears import reg, sim
from pygears.lib import collect, drv, flatten
from pygears.sim import cosim, log
from pygears.sim.sim import sim_assert
from pygears.typing import Array, Int, Queue
from pygears_dsp.lib.matrix_ops.matrix_multiplication import (
    TCfg, matrix_multiplication)
from pygears_dsp.lib.matrix_ops.mult_by_column import column_multiplication
from conftest import set_seed


def create_valid_cfg(cols_per_row, mat1):
    print(mat1)
    num_rows, num_cols = np.squeeze(mat1).shape
    cfg = {
        "cols_per_row": cols_per_row,
        "num_rows": num_rows,
        "num_cols": num_cols,
        'cols_per_multiplier': num_rows // cols_per_row
    }
    return cfg


def run_matrix(impl, mat1, mat2, cols_per_row, col_only: bool = False):
    reg['trace/level'] = 0
    reg['gear/memoize'] = False
    # Add one more dimension to the matrix to support input type for design
    mat1 = mat1.reshape(1, mat1.shape[0], mat1.shape[1])
    mat2 = mat2.reshape(mat2.shape[0], 1, mat2.shape[1])

    # configuration driving
    cfg = create_valid_cfg(cols_per_row, mat1)
    cfg_drv = drv(t=TCfg, seq=[cfg])

    row_t = Queue[Array[Int[16], cfg['num_cols']]]
    mat1_drv = drv(t=Queue[row_t], seq=[mat1])
    res_list = []

    if col_only:
        # remove the extra dimension that was previously added since colum mult accepts
        mat2 = np.squeeze(mat2)
        # for columtn multiplication second operand needs to be only one row
        mat2_drv = drv(t=row_t, seq=[mat2])
        res = column_multiplication(cfg_drv, mat1_drv, mat2_drv)
        # column multiplication returns result in a queue so flatening makes it a regular list
        collect(res | flatten, result=res_list)
        if impl == 'hw':
            cosim('/column_multiplication',
                  'verilator',
                  outdir='/tmp/column_multiplication',
                  rebuild=True,
                  timeout=100)
    else:
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
    try:
        sim()
        # convert PG results into regular 'int'

        if col_only:
            pg_res = [int(el) for el in res_list]
        else:
            pg_res = [int(el) for row_chunk in res_list for el in row_chunk]

        # calculate reference NumPy resutls
        np_res = np.dot(np.squeeze(mat1), np.transpose(mat2.squeeze()))
        # reshape PG results into the same format as
        pg_res = np.array(pg_res).reshape(np_res.shape)
        sim_assert(
            np.equal(pg_res, np_res).all(), "Error in compatring results")
        log.info("\033[92m //==== PASS ====// \033[90m")

    except:
        # printing stack trace
        traceback.print_exc()
        log.info("\033[91m //==== FAILED ====// \033[90m")


@pytest.mark.parametrize('num_cols', [2, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize('num_rows', [2, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize('cols_per_row', [1])
@pytest.mark.parametrize('impl', ['high', 'hw'])
def test_matrix_mult(impl, num_cols, num_rows, cols_per_row, seed):
    set_seed(seed)
    mat1 = np.random.randint(256, size=(num_cols, num_rows))
    mat2 = np.random.randint(256, size=(num_cols, num_rows))
    # if incompatible cols_per_row fall back to '1'
    if mat1.shape[0] % cols_per_row != 0:
        cols_per_row = 1
    run_matrix(impl, mat1, mat2, cols_per_row, col_only=False)


@pytest.mark.parametrize('cols_per_row', [2, 3, 4, 5])
@pytest.mark.parametrize('impl', ['high', 'hw'])
def test_matrix_mult_cols(impl, cols_per_row, seed):
    set_seed(seed)
    # generate random number of colls compatible with colls_per_row
    num_cols = np.random.randint(1, 3) * cols_per_row
    num_rows = np.random.randint(2, cols_per_row * 2)
    # genrate matrixes with random signed numbers 10 bit
    mat1 = np.random.randint(-1023, 1024, size=(num_cols, num_rows))
    mat2 = np.random.randint(-1023, 1024, size=(num_cols, num_rows))

    run_matrix(impl, mat1, mat2, cols_per_row, col_only=False)


@pytest.mark.parametrize('num_cols', [2, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize('num_rows', [2, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize('cols_per_row', [1])
@pytest.mark.parametrize('impl', ['high', 'hw'])
def test_column_multiplicator(impl, num_cols, num_rows, cols_per_row, seed):
    set_seed(seed)
    res_list = []

    mat1 = np.random.randint(256, size=(num_cols, num_rows))
    mat2 = np.random.randint(256, size=(num_cols, num_rows))

    run_matrix(impl, mat1, mat2, cols_per_row, col_only=True)


# run individual test with python command
if __name__ == '__main__':
    reg['debug/trace'] = ['*']
    reg['debug/webviewer'] = True

    try:
        ## HINT : for debugging individual tests
        test_column_multiplicator('sim', 3, 3, 1, 1)
        # test_matrix_mult('sim',num_cols=3,num_rows=3,cols_per_row=1,seed=1)
        # test_matrix_mult_cols('hw', 5, 1)
        # log.info("\033[92m //==== PASS ====// \033[90m")
    except:
        # printing stack trace
        traceback.print_exc()
        log.info("\033[91m //==== FAILED ====// \033[90m")