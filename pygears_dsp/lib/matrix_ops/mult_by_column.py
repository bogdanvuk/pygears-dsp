from pygears.sim import clk
from pygears.lib import flatten, queuemap, mul, dreg,\
    decouple, sdp, qrange,  buff, project, czip, ccat, arraymap, add
from pygears.typing import Int, Array, Tuple, Queue, Uint, trunc
from pygears import gear, datagear
from pygears.util.hof import oper_tree


@gear
def mul_add(din: Array[Tuple[Int, Int], 'd']):
    mult = din \
        | arraymap(f=mul) \
        | dreg

    return oper_tree([m for m in mult], lambda *a: dreg(add(*a)))


@gear
def dot(din: Queue[Array[Tuple[Int, Int], 'd']]):
    return din \
        | dreg \
        | queuemap(f=mul_add, balance=decouple(depth=16, latency=2))


@gear(hdl={'compile': True})
async def vent(write_data, reader) -> b'(write_data, Queue[reader.data])':
    async for data in write_data:
        yield data, None

    await clk()

    async for r, last in reader:
        yield None, (r, all(last))


@gear(hdl={'compile': True})
async def qreplicate(din: Queue, repl_num) -> b'Queue[din.data, din.lvl+1]':
    async with repl_num as rep:
        async for data, eot in din:
            async for tmp, repl_eot in qrange(rep):
                yield data, eot @ repl_eot
                if repl_eot:
                    await clk()


@gear(hdl={'compile': True})
async def rd_req_column_iter(cfg) -> Queue[Uint[16], 2]:
    async with cfg as c:
        async for row_n, row_eot in qrange(c["num_rows"]):
            async for col_n, col_eot in qrange(c["cols_per_multiplier"]):
                    yield trunc(col_n, Uint[16]), row_eot @ col_eot


@gear(hdl={'compile': True})
async def wr_column_req(din: Queue, *, w_addr) -> Tuple[Uint['w_addr'], 'din.data']:
    cnt = Uint[w_addr](0)
    async for d, _ in din:
        yield cnt, d
        cnt += 1


@datagear
def array_zip(din) -> b'Array[Tuple[din[0].data, din[1].data], len(din[0])]':
    res = [(din[0][i], din[1][i]) for i in range(len(din[0]))]
    return res


@gear
def column_multiplication(
    cfg,
    row: Queue[Array[Int[16], 'd'], 2],
    column: Queue[Array[Int[16], 'd'], 1],
):
    """Column_multiplication is module that multiplies one row
        with one column at the time, it can also store several columns in it."""

    # We want to send every row cols_per_multiplier times
    row = row | project | qreplicate(repl_num=cfg['cols_per_multiplier']) | flatten
    reader = rd_req_column_iter(cfg | buff)
    # First we want to write to SDP all columns, then we can start to read them, and do multiplication
    column, rd_vent = vent(column, reader | decouple)

    write_data = wr_column_req(column, w_addr=reader.dtype.data.width)

    column_for_mult = rd_vent | queuemap(f=sdp(write_data), balance=decouple) | dreg
    dot_data, dot_eot = czip(row | dreg | decouple(latency=2, depth=8),
                             column_for_mult) | queuemap(f=array_zip)

    dot_in = ccat(dot_data, dot_eot) | Queue | decouple
    res = dot_in | dot
    return res | decouple
