all: thesis.pdf

clean:
	rm -f thesis.pdf

thesis.pdf: *.tex sections/*.tex
	latexmk -pdflua thesis.tex

preview:
	latexmk -f -pdflua -pvc thesis.tex

check:
	checkwriting thesis.tex sections/{introduction,preliminaries,implementation,experiments,discussion,conclusion,appendix}.tex
