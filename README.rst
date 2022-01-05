pygears-dsp
===========

## Instalation
```sh 
// when in root pygears-dsp dir
pip install -e . 
// alternativelly 
pip3 install -e .
```
- all dependencies should be chekced and installed
Trial:
```sh 
cd tests
python test_fir_single.py
// alternativelly 
python3 test_fir_single.py
```

## Directory structure
- pygears-dsp/lib -> all avalable library functionalities
- tests  ->  all tests that showcase library functions usage


## Run examples
-- Basic - single test run
```sh
cd tests
python <test_name>_single.py 
```
-- Advanced - multiple tests Run using PyTest
```sh
cd tests
pytest <test_name>_regression.py [options]
```

