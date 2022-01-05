from pygears import gear
from pygears.typing import Ufixp
from enum import IntEnum
from pygears.lib import trunc, saturate, qround, pipeline, ccat, field_sel


class Overflow(IntEnum):
    WRAP_AROUND = 0
    SATURATE = 1


class Quantization(IntEnum):
    TRUNCATE = 0
    ROUND = 1


class Operation(IntEnum):
    ADD = 0
    SUB = 1


@gear
def mult_dsp(a, b, *, t=None, quantization=Quantization.TRUNCATE, overflow=Overflow.WRAP_AROUND, latency=0):
    """
    Computes the product of the data on its inputs. Inputs can be of Integer or Fixed point type.

    Parameters
    ----------
    t - Desired output data type. If omitted, output type will be infered from input types.

    quantization - Desired method for reducing the fractional portion of the product.
                   Quantization.TRUNCATE | Quantization.ROUND

    overflow - Desired method for dealing with overflow.
               Overflow.WRAP_AROUND | Overflow.SATURATE

    latency - Number of clock cycles by which the output is delayed.

    Example
    -------
    mult_dsp(din0, din1,
             t=Fixp[6, 14],
             overflow=Overflow.SATURATE,
             quantization=Quantization.ROUND,
             latency=4)
    """
    prod = a * b

    if t is None:
        res = prod
    elif type(t).__base__.__name__ == 'IntegerType':
        if overflow == Overflow.WRAP_AROUND:
            res = trunc(prod, t=t)
        elif overflow == Overflow.SATURATE:
            res = saturate(prod, t=t)
        else:
            raise Exception(f"Parameter overflow has to be chosen from Overflow.WRAP_AROUND|SATURATE")
    elif type(t).__base__.__name__ == 'FixpnumberType':

        if quantization == Quantization.TRUNCATE:
            quant_prod = trunc(prod, t=t.base[prod.dtype.integer, prod.dtype.integer + t.fract])
        elif quantization == Quantization.ROUND:
            quant_prod = qround(prod, fract=t.fract)
        else:
            raise Exception(f"Parameter quantization has to be chosen from Quantization.TRUNCATE|ROUND")
        
        if overflow == Overflow.WRAP_AROUND:
            res = trunc(quant_prod, t=t)
        elif overflow == Overflow.SATURATE:
            res = saturate(quant_prod, t=t)
        else:
            raise Exception(f"Parameter overflow has to be chosen from Overflow.WRAP_AROUND|SATURATE")
    else:
        raise Exception('t has to be either IntegerType or FixpnumberType')
    
    if latency:
        return res | pipeline(length=latency)
    else:
        return res


@gear
def add_sub_dsp(a, b, *, t=None, quantization=Quantization.TRUNCATE, overflow=Overflow.WRAP_AROUND, latency=0, operation=Operation.ADD):
    """
    Computes the sum/difference of the data on its inputs. Inputs can be of Integer or Fixed point type.
    In case of subtraction, first input is the minuend, while second input is the subtrahend.

    Parameters
    ----------
    t - Desired output data type. If omitted, output type will be infered from input types.

    operation - Specifies the operation to be either addition or subtraction.
                Operation.ADD | Operation.SUB

    quantization - Desired method for reducing the fractional portion of the product.
                   Quantization.TRUNCATE | Quantization.ROUND

    overflow - Desired method for dealing with overflow.
               Overflow.WRAP_AROUND | Overflow.SATURATE

    latency - Number of clock cycles by which the output is delayed.

    Example
    -------
    add_sub_dsp(din0, din1,
             t=Fixp[6, 14],
             operation=Operation.ADD,
             overflow=Overflow.SATURATE,
             quantization=Quantization.ROUND,
             latency=4)
    """

    if operation == Operation.ADD:
        prod = a + b
    elif operation == Operation.SUB:
        prod = a - b
    else:
        raise Exception(f"Parameter operation has to be chosen from Operation.ADD|SUB")

    if t is None:
        res = prod
    elif type(t).__base__.__name__ == 'IntegerType':
        if overflow == Overflow.WRAP_AROUND:
            res = trunc(prod, t=t)
        elif overflow == Overflow.SATURATE:
            res = saturate(prod, t=t)
        else:
            raise Exception(f"Parameter overflow has to be chosen from Overflow.WRAP_AROUND|SATURATE")
    elif type(t).__base__.__name__ == 'FixpnumberType':

        if quantization == Quantization.TRUNCATE:
            quant_prod = trunc(prod, t=t.base[prod.dtype.integer, prod.dtype.integer + t.fract])
        elif quantization == Quantization.ROUND:
            quant_prod = qround(prod, fract=t.fract)
        else:
            raise Exception(f"Parameter quantization has to be chosen from Quantization.TRUNCATE|ROUND")

        if overflow == Overflow.WRAP_AROUND:
            res = trunc(quant_prod, t=t)
        elif overflow == Overflow.SATURATE:
            res = saturate(quant_prod, t=t)
        else:
            raise Exception(f"Parameter overflow has to be chosen from Overflow.WRAP_AROUND|SATURATE")
    else:
        raise Exception('t has to be either IntegerType or FixpnumberType')

    if latency:
        return res | pipeline(length=latency, feedback=True)
    else:
        return res
    
    
@gear
def mux_dsp(sel, *din):
    """
    Selects one data input to be propagated to output based on the value of sel input.

    Example
    -------
    mux_dsp(sel, din0, din1)
    """
    return field_sel(sel, ccat(*din))
