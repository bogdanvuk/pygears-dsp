from pygears_dsp.lib.matrix_ops.mult_by_column import column_multiplication

from pygears import gear
from pygears.lib import flatten, ccat, dreg, decouple, dispatch, qdeal, group, sieve
from pygears.typing import Array, Tuple, Uint, Tuple

TCfg = Tuple[{
    'cols_per_row': Uint[8],
    'num_rows': Uint[8],
    'num_cols': Uint[8],
    'cols_per_multiplier': Uint[8]
}]


@gear(hdl={'compile': True})
async def row_dispatch(din, *, cols_per_row) -> Tuple['din', Uint['cols_per_row']]:
    async for data, eot in din:
        yield (data, eot), Uint[cols_per_row].max


@gear
def matrix_multiplication(cfg, mat1, mat2, *, cols_per_row):
    """General idea is to parallelize matrix multiplication, this is achieved by
        multiplying one row with several columns at the same time. Number of columns that
        are multiplied with one row is cols_per_row. Column_multiplication is module that multiplies one row
        with one column at the time, it can also store several columns in it.
        First we need to split mat2 by columns and send them to different column_multiplication modules, to be stored,
        then send every row on each column_multiplication."""
    col_chunks = qdeal(mat2, num=cols_per_row, lvl=1)
    row_chunks = row_dispatch(mat1, cols_per_row=cols_per_row) \
        | dreg \
        | decouple(latency=2) \
        | dispatch
    tmp = []
    if not isinstance(col_chunks, tuple):
        col_chunks = (col_chunks, )
    if not isinstance(row_chunks, tuple):
        row_chunks = (row_chunks, )

    for col, row in zip(col_chunks, row_chunks):
        # col is flattened because, after qdeal, every col has type Queue lvl1 with eot == True
        # after flattening, we group it by cols_per_multiplier (set eot (last) after last column that goes
        # to specific column multiplier)
        col = col | flatten | group(size=cfg['cols_per_multiplier'])
        tmp.append(column_multiplication(cfg, row, col) | flatten)

    res = ccat(*tmp) | Array
    return res
