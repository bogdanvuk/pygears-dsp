from pygears import gear
from pygears.typing import Tuple, Uint
from pygears.lib import cart, fmap, lt, rng

TCfg = Tuple[{'period': Uint['w_period'], 'width': Uint['w_width']}]


@gear
def pulse(cfg: TCfg):
    """Generates pulse of variable length,
    'width' is clk cycles for pulse width"""
    cnt = rng(0, cfg['period'], 1)
    return cart(cnt, cfg['width']) | fmap(f=lt)
