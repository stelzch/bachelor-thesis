all: thesis.pdf

clean:
	rm -f thesis.pdf

thesis.pdf: thesis.tex
	latexmk -pdf thesis.tex

check:
	checkwriting thesis.tex sections/{introduction,preliminaries,implementation,experiments,discussion,conclusion,appendix}.tex
