from pygears import gear
from pygears.lib import dreg


@gear
def fir_direct(din, *, b):
    reg_s = din
    add_s = reg_s * b[0]
    for coef in b[1:]:
        reg_s = reg_s | dreg(init=0)
        add_s = add_s + (reg_s * coef)

    return add_s


@gear
def fir_transposed(din, *, b):
    reg_s = din * b[0]
    for coef in b[1:]:
        gain_s = din * coef
        reg_s = gain_s + (reg_s | dreg(init=0))

    return reg_s
