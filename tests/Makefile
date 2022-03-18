.PHONY: help
opts =
logdir = "build/pytest.log"
save_to = #| tee $(logdir)

help:           ## Show this help.
	## options:
		## opts=<pytest options (default options like '-x' '-s' etc...)>
			## '--num=10' -> number of seeds to run per test
			## '--random=1' -> run randomized seeds
			## '--seed=1234' -> run specific seed
			## '--cosim=0' -> disable cosim, by default enabled
		## logdir=<location where to save log>
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

fir:			## run IIR filter tests once
	pytest $(opts) test_fir_regression.py $(save_to)

fir_regr:		## run IIR filter test in a regression
	pytest test_fir_regression.py::test_fir_random --num=1 
	pytest test_fir_regression.py::test_fir_random_type --num=50 --random=1 $(save_to)
	pytest test_fir_regression.py::test_fir_limits --num=3 --random=1 $(save_to)
	pytest test_fir_regression.py::test_fir_sine --num=3 --random=1 $(save_to)

iir:			## run IIR filter tests once
	pytest $(opts) test_iir_regression.py $(save_to)

cordic: 		## run cordic filter tests once
	pytest $(opts) test_cordic_regression.py $(save_to)

matrix: 		## run matrix_ops tests ondce
	pytest $(opts) test_matrix_ops_regression.py $(save_to)

all: fir iir cordic matrix

sanity:			## run all available files once for sanity
	python3 $(opts) test_cordic_regression.py 
	python3 $(opts) test_fir_regression.py
	python3 $(opts) test_iir_regression.py
	python3 $(opts) test_matrix_ops_regression.py
	python3 $(opts) test_fft_bf_single.py
	python3 $(opts) test_fir_single.py
	python3 $(opts) test_iir_single.py
	python3 $(opts) test_matrix_ops_single.py

