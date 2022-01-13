'''
conftest.py 
'''
import logging
import numpy as np
import random
from math import log, pi, sin

from pygears import reg
# in pytest clear pygears tree between tests to allow running mutliple tests
from pygears.util.test_utils import clear
from pygears.util.test_utils import synth_check_fixt, lang

import pytest


def pytest_addoption(parser):
    parser.addoption('--cosim', action='store')
    parser.addoption('--seed', action='store')
    parser.addoption('--num', action='store')
    parser.addoption('--random', action='store')
    # parser.addoption('--dbginfo', action = 'store')


def pytest_generate_tests(metafunc):
    seed_value = metafunc.config.option.seed
    test_num_value = metafunc.config.option.num
    random_value = metafunc.config.option.random
    cosim_value = metafunc.config.option.cosim
    # dbginfo_value = metafunc.config.option.dbginfo

    # print(f' dbgfo :{dbginfo_value}')
    # if dbginfo_value == 1:
    #     print(f' changing dbgfo :{dbginfo_value}')
    #     reg['logger/sim/level'] = logging.DEBUG
    # print(f"re {reg['logger/sim/level']}")

    if 'do_cosim' in metafunc.fixturenames:
        mark = metafunc.definition.get_closest_marker('parametrize')
        # check if do_cosim was already parametrize in the test itself
        print("-----------------------------", mark)
        if mark is not None:
            print(mark.args[0])
        if not mark or 'do_cosim' not in mark.args[0]:
            if cosim_value is not None:
                if int(cosim_value) == 1:
                    metafunc.parametrize("do_cosim", [True])
                elif int(cosim_value) == 0:
                    metafunc.parametrize("do_cosim", [False])
            else:
                metafunc.parametrize("do_cosim", [True, False])

    if 'seed' in metafunc.fixturenames:
        if seed_value is not None:
            if seed_value == 'random':
                seed_value = None  # seed will be randomized
            metafunc.parametrize("seed", [seed_value])
        else:
            if test_num_value is not None:
                if (random_value is not None):
                    metafunc.parametrize("seed", [
                        random.randrange(100_000_000)
                        for i in range(int(test_num_value))
                    ])
                else:
                    metafunc.parametrize("seed",
                                         list(range(int(test_num_value))))
            else:  # default seed will be set to '1'
                metafunc.parametrize("seed", [1])


def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    print(f'setup_module : {module}')


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method."""


def sine_seq(freq, fsample, num, t_b):
    """[Return sequence of float nubers as sine signal]

    Args:
        freq ([uns integer]): [clock freequency]
        fsample ([uns integer]): [sampling frequency]
        num ([uns integer]): [number of items to generate]
        t_b ([Fixp]): [item type used to saturate if needed]

    Returns:
        [list of floats]: [sequence as list of items in range [-1,t_b.fmax]]
    """
    seq = []
    for n in range(num):
        val = sin(2 * pi * freq / fsample * n)
        if val == 1:  # saturate to fmax if sine reaches '1'
            val = t_b.fmax
        seq.append(val)
    return seq


def random_seq(fixp_t, num=1):
    """Return defined numbert of random signal items of Fixp type"""
    seq = []
    for i in range(num + 1):
        seq.append(np.random.uniform(fixp_t.fmin, fixp_t.fmax))
    return seq


def random_choice_seq(seq_list, num):
    seq = []
    for i in range(10):
        choice = random.choice(range(len(seq_list)))
        seq.extend(seq_list[choice])
    return seq


def constant_seq(fixp_t, num=1, val=None):
    """Return constant signal as a sequence depending of Fixp type"""
    seq = []
    if val == None:
        val = np.random.uniform(fixp_t.fmin, fixp_t.fmax)
    for i in range(num):
        seq.append(val)
    return seq


def set_seed(seed):
    """Unify all seeds"""
    reg['sim/rand_seed'] = seed
    random.seed(reg['sim/rand_seed'])
    np.random.seed(seed)


def fixp_sat(f_type, val):
    try:
        # try to convert to filter implementation output type
        f_type(val)
    except ValueError:
        if (val > 0):
            val = f_type.fmax
        elif (val < 0):
            val = f_type.fmin
        else:
            log.error(f'Error when converting result {val} to {f_type}')
    return val