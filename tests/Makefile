.PHONY: help
opts =
logdir = "build/pytest.log"
save_to = #| tee $(logdir)

help:           ## Show this help.
	## options:
		## opts = <pytest options (default options like '-x' '-s' etc...)>
			## --num=10 -> number of seeds to run per test
			## --random=1 -> run randomized seeds
			## --seed=1234 -> run specific seed
			## --cosim=0 -> disable cosim, by default enabled
		## logdir = <location where to save log>
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

fir:			## run IIR filter tests once
	pytest $(opts) test_fir.py $(save_to)

fir_regr:		## run IIR filter test in a regression
	pytest $(opts) test_fir.py::test_fir_random --num=50 --random=1 $(save_to}
	pytest $(opts) test_fir.py::test_fir_random_type --num=50 --random=1 $(save_to)
	pytest $(opts) test_fir.py::test_fir_limits --num=3 --random=1 $(save_to)
	pytest $(opts) test_fir.py::test_fir_sine --num=3 --random=1 $(save_to)


iir:			## run IIR filter tests once
	pytest $(opts) test_iir.py $(save_to)

cordic: 		## run cordic filter tests once
	pytest $(opts) test_cordic.py $(save_to)
