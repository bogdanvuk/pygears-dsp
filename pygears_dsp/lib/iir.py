from pygears import gear, Intf
from pygears.lib import dreg, decouple, saturate, qround


@gear
def iir_1dsos(din, *, a, b, gain):

    # add input gain and init delayed inputs
    zu0 = din * gain
    zu1 = zu0 | dreg(init=0)
    zu2 = zu1 | dreg(init=0)

    # perform b coefficient sum
    a1 = (zu1 * b[1]) + (zu2 * b[2])
    a2 = a1 + (zu0 * b[0])

    # declare output interface and its type
    y = Intf(a2.dtype)

    # init delayed outputs
    zy1 = y | decouple(init=0)
    zy2 = zy1 | dreg(init=0)

    # perform a coefficient sum
    b1 = (zy2 * a[2]) + (zy1 * a[1])

    # add both sums and set output
    y |= (a2 - b1) | qround(fract=a2.dtype.fract) | saturate(t=a2.dtype)
    return y


@gear
def iir_2tsos(din, *, a, b, gain):

    # add input gain
    x = din * gain

    # declare output interface and its type
    y = Intf(din.dtype)

    # perform first tap multiplication and sum
    z0 = ((x * b[2]) - (y * a[2]))

    # delay first sum output
    z0_delayed = z0 | dreg(init=0)

    # perform second tap multiplication and sum
    z1 = ((x * b[1]) + z0_delayed - (y * a[1]))

    # delay second sum output
    z1_delayed = z1 | decouple(init=0)

    # perform final sum and set output
    y |= ((x * b[0]) + z1_delayed) | qround(fract=din.dtype.fract) | saturate(t=din.dtype)
    return y


@gear
def iir_df1dsos(din, *, a, b, gain, ogain):

    # init temp
    temp = din

    # add cascades for all b coefficients
    for i in range(len(b)):

        # format every cascaded output as input
        temp = temp | iir_1dsos(a=a[i], b=b[i], gain=gain[i]) | qround(fract=din.dtype.fract) | saturate(t=din.dtype)

    # add output gain and format as input
    dout = (temp * ogain) | qround(fract=din.dtype.fract) | saturate(t=din.dtype)
    return dout


@gear
def iir_df2tsos(din, *, a, b, gain, ogain):

    # init temp
    temp = din

    # add cascades for all b coefficients
    for i in range(len(b)):

        # format every cascaded output as input
        temp = temp | iir_2tsos(a=a[i], b=b[i], gain=gain[i])

    # add output gain and format as input
    dout = (temp * ogain) | qround(fract=din.dtype.fract) | saturate(t=din.dtype)
    return dout
