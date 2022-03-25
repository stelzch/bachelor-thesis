all: thesis.pdf

clean:
	latexmk -CA thesis

figures:
	python3 scripts/benchmark_plot.py
	python3 scripts/buffer_sizes.py
	python3 scripts/scaling_plot.py

thesis.pdf: *.tex sections/*.tex figures
	latexmk -pdflua thesis.tex

preview:
	latexmk -f -pdflua -pvc thesis.tex

check:
	checkwriting thesis.tex sections/{introduction,preliminaries,implementation,experiments,discussion,conclusion,appendix}.tex
