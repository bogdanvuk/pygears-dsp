from pygears import gear
from pygears.typing import Tuple, Uint
from pygears.lib import cart, fmap, gt, rng

TCfg = Tuple[{'period': Uint['w_period'], 'width': Uint['w_width']}]


@gear
def pulse(cfg: TCfg):
    """Generates pulse of variable length,
    width is clk cycles for value 0"""
    cnt = rng(0, cfg['period'], 1)
    return cart(cnt, cfg['width']) | fmap(f=gt)
