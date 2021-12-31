from pygears import gear
from pygears.lib import dreg, qround, saturate


@gear
def fir_direct(din, *, b):

    # init delayed input and output sum
    x = din
    y_sum = x * b[0]

    # construct filter structure for all fir coefficients
    for b_coef in b[1:]:

        # add delay
        x = x | dreg(init=0)

        # summation
        y_sum = y_sum + (x * b_coef)

    # format sum as input
    return y_sum | qround(fract=din.dtype.fract) | saturate(t=din.dtype)


@gear
def fir_transposed(din, *, b):

    # init output sum
    y_sum = din * b[0]

    # construct filter structure for all fir coefficients
    for b_coef in b[1:]:

        # multiply input with b coefficient
        mult_b_result = din * b_coef

        # delay output sum
        delayed_y_sum = y_sum | dreg(init=0)

        # add to output sum
        y_sum = mult_b_result + delayed_y_sum

    # format sum as input
    return y_sum | qround(fract=din.dtype.fract) | saturate(t=din.dtype)
