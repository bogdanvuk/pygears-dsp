import traceback
from pygears.typing import Fixp, Array, code
from pygears.lib import drv, check, serialize, flatten, collect
from pygears.sim import sim, cosim, log
from pygears_dsp.lib.fft_bf import FFT_list, FFT_recursive
from scipy.fft import fft
from pygears import reg
import math

########################## DESIGN CONTROLS ##########################
stages = 3
Wn_fixp_size = [1, 8]
input_fixp_size = [1, 8]
output_fixp_size = [3, 8]
########################### TEST CONTROLS ###########################
dut_select = 0  # 0 = FFT_list, 1=FFT_recursive
sv_gen = 1
tolerated_output_difference = 1e-1
###########################################################################
# probe all signals
reg['debug/trace'] = ['*']
# enable webviewer support
reg['debug/webviewer'] = True

# helpers
D = 2**stages


def round_to_fixp(din, t):
    rounded = din * (2**t.fract) // 1
    if rounded == 2**(t.width - 1):
        rounded -= 1
    return code(int(rounded), cast_type=t)


# type definitions
Wn_num_type = Fixp[Wn_fixp_size[0], Wn_fixp_size[1]]
input_num_type = Fixp[input_fixp_size[0], input_fixp_size[1]]
output_num_type = Fixp[output_fixp_size[0], output_fixp_size[1]]
input_point_type = Array[input_num_type, 2]
input_seq_type = Array[input_point_type, D]
Wn_pair_type = Array[Wn_num_type, 2]
Wn_type = Array[Wn_pair_type, D]

# compile-time parameters
Wn = Wn_type([[
    round_to_fixp(math.cos(2 * math.pi * i / D), t=Wn_num_type),
    round_to_fixp(-math.sin(2 * math.pi * i / D), t=Wn_num_type)
] for i in range(D)])

# define parameter list for FFT_list
s1_ix = [0, 0, 2, 2, 1, 1, 3, 3]
s2_ix = [0, 1, 0, 1, 4, 5, 4, 5]
s3_ix = [0, 1, 2, 3, 0, 1, 2, 3]
fft_list_fixed_3stage = Array[Array[Array[int, D], 3], stages]([
    [  # stage 1
        [i for i in s1_ix], [i + 4 for i in s1_ix],
        [i % 2 * 4 for i in range(8)]
    ],
    [  # stage 2
        [i for i in s2_ix], [i + 2 for i in s2_ix],
        [i % 4 * 2 for i in range(8)]
    ],
    [  # stage 3
        [i for i in s3_ix], [i + 4 for i in s3_ix], [i for i in range(8)]
    ]
])

# test inputs
input_points = [i / D for i in range(D)]
input_seq = []
ix = 0
for input_points_ix in input_points:
    input_seq.append(input_point_type([input_points_ix, 0]))
    ix += 1
test_input = drv(t=input_seq_type, seq=[input_seq])

# test expected outputs
exp_res = []
calc_res = fft(input_points)
for calc_res_i in calc_res:
    exp_res.append(calc_res_i.real)
    exp_res.append(calc_res_i.imag)

# # connect DUT
if dut_select == 0:
    FFT_list(din=test_input,
             index_lists=fft_list_fixed_3stage,
             Wn=Wn,
             output_dtype=output_num_type) \
    | serialize | flatten | serialize | flatten \
    | check(ref=exp_res, cmp=lambda x, y: abs(x - y) < tolerated_output_difference)

    if sv_gen:
        cosim('FFT_list', 'verilator', outdir='build/fft_bf/rtl', timeout=10)
else:
    FFT_recursive(a_input_i=test_input,
                  N=D,
                  Wn=Wn,
                  output_dtype=output_num_type) \
    | serialize | flatten | serialize | flatten \
    | check(ref=exp_res, cmp=lambda x, y: abs(x - y) < tolerated_output_difference)
    if sv_gen:
        cosim('FFT_recursive',
              'verilator',
              outdir='build/fft_bf/rtl',
              timeout=10)

# start test

try:
    sim('build/fft_bf/')
    log.info("\033[92m //==== PASS ====// \033[90m")
except:
    # printing stack trace
    traceback.print_exc()
    log.info("\033[91m //==== FAILED ====// \033[90m")
