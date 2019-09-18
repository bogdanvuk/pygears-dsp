from pygears import gear, Intf
from pygears.typing import Fixp
from pygears.lib import dreg, decouple

@gear
def iir_1dsos(din, *, a, b, gain):
    din = din * gain
    zu1 = din | dreg(init=0)
    zu2 = zu1 | dreg(init=0)

    a1 = (zu1 * b[1]) + (zu2 * b[2])
    a2 = a1 + (din*b[0])

    y = Intf(a2.dtype*2)

    zy1 = y | a2.dtype | decouple(init=0)
    zy2 = zy1 | dreg(init=0)
    a3 = (zy2 * a[2]) + (zy1 * a[1])
    y |= a2 - a3

    return y

@gear
def iir_2tsos(din, *, a, b, gain):
    din = din * gain
    y = Intf(din.dtype*5)
    a1 = ((din * b[2]) - (y * a[2]))
    z1 = a1 | dreg(init=0)
    z2 = ((din * b[1]) + z1 - (y * a[1])) | decouple(init=0)
    y |= (din*b[0]) + z2

    return y

@gear
def iir_df1dsos(din, *, a, b, gain, ogain):
    dout = din
    for i in range(len(b)):
        dout = dout | iir_1dsos(a=a[i], b=b[i], gain=gain[i])

    dout = dout * ogain
    return dout

@gear
def iir_df2tsos(din, *, a, b, gain, ogain):
    dout = din
    for i in range(len(b)):
        dout = dout | iir_2tsos(a=a[i], b=b[i], gain=gain[i])

    dout = dout * ogain
    return dout
