#!/usr/bin/env python3

import random
import traceback

import numpy as np
from pygears.sim.sim import sim_assert
import pytest

from pygears import reg, sim
from pygears.lib import collect, drv, flatten
from pygears.sim import cosim, log
from pygears.typing import Array, Int, Queue
from pygears_dsp.lib.matrix_ops.matrix_multiplication import (
    TCfg, matrix_multiplication)
from pygears_dsp.lib.matrix_ops.mult_by_column import column_multiplication
from conftest import set_seed


def matrix_ops_single():
    ########################## DESIGN CONTROLS ##########################
    num_cols = 8
    num_rows = 6  # HINT suppoerted all dimesitions > 1
    cols_per_row = 2  # HINT suported values that are divisible with num_colls
    ########################### TEST CONTROLS ###########################
    sv_gen = 1
    ###########################################################################
    # set either random or custom seed
    seed = random.randrange(0, 2**32, 1)
    # seed = 1379896999

    # """Unify all seeds"""
    log.info(f"Random SEED: {seed}")
    set_seed(seed)

    ## input randomization
    mat1 = np.random.randint(128, size=(num_rows, num_cols))
    mat2 = np.random.randint(128, size=(num_rows, num_cols))
    mat1 = np.ones((num_rows, num_cols))
    mat2 = np.ones((num_rows, num_cols))

    # input the constatn value optionally
    # mat1 = np.empty((num_rows, num_cols))
    # mat2 = np.empty((num_rows, num_cols))
    # # fill the matrix with the same value
    # mat1.fill(32767)
    # mat2.fill(-32768)

    print("Inputs: ")
    print(type(mat1))
    print(mat1)
    print(type(mat2))
    print(mat2)

    reg['trace/level'] = 0
    reg['gear/memoize'] = False

    reg['debug/trace'] = ['*']
    reg['debug/webviewer'] = True
    res_list = []

    cfg = {
        "cols_per_row": cols_per_row,
        "num_rows": num_rows,
        "num_cols": num_cols,
        'cols_per_multiplier': num_rows // cols_per_row
    }
    cfg_seq = [cfg]
    cfg_drv = drv(t=TCfg, seq=cfg_seq)

    # Add one more dimenstion to the matrix to support input type for design
    mat1 = mat1.reshape(1, mat1.shape[0], mat1.shape[1])
    mat2 = mat2.reshape(mat2.shape[0], 1, mat2.shape[1])
    mat1_seq = [mat1]
    mat2_seq = [mat2]

    row_t = Queue[Array[Int[16], cfg['num_cols']]]
    mat1_drv = drv(t=Queue[row_t], seq=mat1_seq)
    mat2_drv = drv(t=Queue[row_t], seq=mat2_seq)
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

    ## Print raw results results
    log.info(f'len_res_list: \n{len(res_list)}')
    try:
        pg_res = [int(el) for row_chunk in res_list for el in row_chunk]
        # calc refference data - matrix2 needs to be transposed before doing multiplocation
        np_res = np.dot(np.squeeze(mat1), np.transpose(mat2.squeeze()))
        pg_res = np.array(pg_res).reshape(np_res.shape)

        log.info(f'result: \n{res}')
        log.info(f'pg_res: \n{pg_res}, shape: {pg_res.shape}')
        log.info(f'np_res: \n{np_res}, shape: {np_res.shape}')
        sim_assert(
            np.equal(pg_res, np_res).all(), "Error in compatring results")
        log.info("\033[92m //==== PASS ====// \033[90m")
    except:
        # printing stack trace
        traceback.print_exc()
        log.info("\033[91m //==== FAILED ====// \033[90m")


if __name__ == '__main__':
    matrix_ops_single()