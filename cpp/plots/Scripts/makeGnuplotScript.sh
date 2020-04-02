#!/bin/bash

nargs=$#
# Arguments should be even and >= 4
if [ $nargs -lt 3 ]
then
    echo "Usage: $0 output xrange xtics yrange title file label cum [file label cum...]"
    exit 0
fi

KEYLW=1

output=$1
shift

if [ "$output" = "term" ]; then
    printf "set terminal wxt size 1200,900 linewidth 7 rounded\n"
    printf "set key font \",20\"\n"
    printf "set xtics font \", 24\"\n"
    printf "set ytics font \", 24\"\n"
    printf "set lmargin 15\n"
    printf "set rmargin 6\n"
    printf "set tmargin 3\n"
    printf "set bmargin 5\n"
    printf "set xtics offset 0,-2,0\n"
else
    printf "set output '$output'\n"

    extension="${output##*.}"
    if [ "$extension" = "png" ]; then
        printf "set terminal pngcairo size 1200,900 linewidth 7 rounded\n"
        printf "set key font \",20\"\n"
        printf "set xtics font \", 24\"\n"
        printf "set ytics font \", 24\"\n"
        printf "set lmargin 15\n"
        printf "set rmargin 6\n"
        printf "set tmargin 3\n"
        printf "set bmargin 5\n"
    elif [ "$extension" = "pdf" ]; then
        printf "set terminal pdfcairo size 12,9 linewidth 7 rounded\n"
        printf "set key font \",40\"\n"
        printf "set xtics font \", 40\"\n"
        printf "set ytics font \", 40\"\n"
        printf "set lmargin 15\n"
        printf "set rmargin 9\n"
        printf "set tmargin 3\n"
        printf "set bmargin 5\n"
        printf "set xtics offset 0,-2,0\n"
    else
        echo "Extension $extension not supported"
        exit 1
    fi
fi

# Define dash types by scratch so we can have the legend with shorter ones.
# These styles try to emulate the default ones
# Note that we ignore 1, 6, 10, 16, ... since those are by default solid lines which are fine.
printf "set dashtype 2 (30,30)\n"
printf "set dashtype 12 (9,9)\n"
printf "set dashtype 3 (7,15)\n"
printf "set dashtype 13 (4,7)\n"
printf "set dashtype 4 (30,15,10,15)\n"
printf "set dashtype 14 (15,7,5,7)\n"
printf "set dashtype 5 (30,15,5,15,5,15)\n"
printf "set dashtype 15 (10,6,2,6,2,5)\n"
# 6, 16 ignored...
printf "set dashtype 7 (30,30)\n"
printf "set dashtype 17 (9,9)\n"
printf "set dashtype 8 (7,15)\n"
printf "set dashtype 18 (4,7)\n"
printf "set dashtype 9 (30,15,10,15)\n"
printf "set dashtype 19 (15,7,5,7)\n"
printf "set dashtype 10 (30,15,5,15,5,15)\n"
printf "set dashtype 20 (10,6,2,6,2,5)\n"

printf "set key reverse Left left top samplen 2.25 box opaque width 1\n"

xrange=$1
shift
xtics=$1
shift
yrange=$1
shift

if [ "$xtics" = "na" ]; then
    xtics=10000
else
    printf "set xtics $xtics\n"
fi

if [ $xtics -ge 10000 ]; then
    printf "set format x \"%%.0t*10^%%T\"\n"
fi

if [ "$xrange" = "na" ]; then
    printf "set xrange [0<*:]\n"
elif [[ "$xrange" =~ ":" ]]; then
    printf "set xrange [$xrange]\n"
else
    printf "set xrange [0:$xrange]\n"
fi
if [ "$yrange" = "na" ]; then
    printf ""
elif [[ "$yrange" =~ ":" ]]; then
    printf "set yrange [$yrange]\n"
else
    printf "set yrange [0:$yrange]\n"
fi

printf "set style fill transparent solid 0.4 noborder\n"
printf "set colorsequence podo\n"
printf "set datafile missing NaN\n"

title=$1
shift

# title and file setup
printf "set title \"$title\"\n"

COUNTER=1

# Setup for required first file (filename, title)
main=2
off=4
if [[ "$3" =~ "1" ]]; then
    ((main++))
    ((off++))
fi

printf "plot '$1' using 1:$main with line smooth csplines ls $COUNTER dt $COUNTER notitle, \\"
printf "\n   NaN with line title '$2' ls $COUNTER dt $((COUNTER+10)) lw $KEYLW"
if [[ "$3" != *"na" ]]; then
    printf ", \\"
    printf "\n   '$1' using 1 : (\$$main-\$$off) : (\$$main+\$$off) with filledcurves ls $COUNTER notitle"
fi
shift
shift
shift

# Iterate over all remaining arguments
while [ $# -ne 0 ]
do
    main=2
    off=4
    if [[ "$3" =~ "1" ]]; then
        ((main++))
        ((off++))
    fi

    COUNTER=$((COUNTER+1))
    printf ", \\"
    printf "\n   '$1' using 1:$main with line smooth csplines ls $COUNTER dt $COUNTER notitle, \\"
    printf "\n   NaN with line title '$2' ls $COUNTER dt $((COUNTER+10)) lw $KEYLW"
    if [[ "$3" != *"na" ]]; then
        printf ", \\"
        printf "\n   '$1' using 1 : (\$$main-\$$off) : (\$$main+\$$off) with filledcurves ls $COUNTER notitle"
    fi
    shift
    shift
    shift
done

# Remember to launch gnuplot with the -p option to see the plots!
printf "\n"
