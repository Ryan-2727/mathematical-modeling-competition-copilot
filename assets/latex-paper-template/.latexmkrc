$pdf_mode = 5;
$xelatex = 'xelatex -synctex=1 -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
$bibtex_use = 2;
$clean_ext .= ' %R.bbl %R.blg %R.fdb_latexmk %R.fls %R.synctex.gz';
