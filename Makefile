all: thesis.pdf figures

clean:
	latexmk -CA thesis

figures:
	python3 scripts/benchmark_plot.py
	python3 scripts/buffer_sizes.py

thesis.pdf: *.tex sections/*.tex
	latexmk -pdflua thesis.tex

preview:
	latexmk -f -pdflua -pvc thesis.tex

check:
	checkwriting thesis.tex sections/{introduction,preliminaries,implementation,experiments,discussion,conclusion,appendix}.tex
