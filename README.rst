================
pygears-dsp
================

A library of different dsp based functions done in PyGears framework

Instalation:
-----------

 // when in root pygears-dsp dir


``pip install -e .``


 // alternativelly 


``pip3 install -e .``



 all dependencies should be chekced and installed
 
Trial if installation is succesfull and package is usable:


 ``cd tests``

 ``python test_fir_single.py``


 // alternativelly 
 
 ``python3 test_fir_single.py``

Directory structure
-----------

- ``pygears-dsp/lib`` -> all avalable library functionalities
- ``tests``  ->  all tests that showcase library functions usage


Run examples
-----------

-- Basic - single test run,all tests in 'test' folder ending with ``_single.py``

``cd tests``

``python <test_name>_single.py``

-- Advanced - multiple tests Run using PyTest, all test files in 'test' folder ending with ``_regression.py``

``cd tests``

``pytest <test_name>_regression.py [options]``

