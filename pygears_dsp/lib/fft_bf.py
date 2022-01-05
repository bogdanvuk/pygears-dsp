from pygears import gear
from pygears.typing import Array
from pygears.lib import ccat, qround, saturate, arraymap, dreg, when


@gear
def FFT_list(din, *, index_lists, Wn, output_dtype):
    for stage in range(len(index_lists)):
        stage_output = []
        for ix in range(2**len(index_lists)):
            stage_output.append(
                butterfly_sum(din[index_lists[stage][0][ix]],
                              din[index_lists[stage][1][ix]],
                              Wn=Wn[index_lists[stage][2][ix]]))
        din = stage_output

    return ccat(*stage_output) | Array | arraymap(f=arraymap(f=format_fixp(
        t=output_dtype)))


@gear
def FFT_recursive(a_input_i: Array, *, N, Wn, output_dtype):
    """https://web.iiit.ac.in/~pratik.kamble/storage/Algorithms/Cormen_Algorithms_3rd.pdf"""  # page 911
    if len(a_input_i.dtype) == 1:
        # TODO: when the issue of passed input interface to output is fixed: remove [:]
        return a_input_i[:]
    else:
        a0_i = []
        a1_i = []
        for i in range(N):
            if i % 2 == 0:
                a0_i.append(a_input_i[i])
            else:
                a1_i.append(a_input_i[i])

        y0_i = FFT_recursive(ccat(*a0_i) | Array,
                             N=N // 2,
                             Wn=Wn,
                             output_dtype=output_dtype)
        y1_i = FFT_recursive(ccat(*a1_i) | Array,
                             N=N // 2,
                             Wn=Wn,
                             output_dtype=output_dtype)

        y_output_i = []
        for k in range(N):
            Wk = Wn[k * (len(Wn) // N)]
            y_output_i.append(
                butterfly_sum(y0_i[k % (N // 2)], y1_i[k % (N // 2)], Wn=Wk))

        return ccat(*y_output_i) | Array


@gear
def butterfly_sum(din0, din1, *, Wn):
    return ccat(din0[0] + (din1[0] * Wn[0]) - (din1[1] * Wn[1]), din0[1] +
                (din1[0] * Wn[1]) + (din1[1] * Wn[0])) | Array


@gear
def format_fixp(din, *, t):
    return din | qround(fract=t.fract) | saturate(t=t)
