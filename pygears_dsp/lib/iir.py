from pygears import gear, Intf
from pygears.lib import dreg, decouple


@gear
def iir_direct1_sos(din, *, a, b, gain):
    din = din * gain

    zu1 = din | dreg(init=0)
    zu2 = zu1 | dreg(init=0)

    a1 = (zu1 * b[1]) + din
    a2 = (zu2 * b[2]) + a1

    y = Intf(a2.dtype)  # type????

    zy1 = y | decouple(init=0)
    zy2 = zy1 | dreg(init=0)

    a3 = a2 - (zy1 * a[1])
    y |= a3 - (zy2 * a[2])

    return y
