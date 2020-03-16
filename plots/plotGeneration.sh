#!/bin/bash

experiments_folder="./experiments"
results_folder="$experiments_folder/results"
plot_folder="$experiments_folder/plots"

mkdir -p "$plot_folder"

if [ $# -eq 0 ]; then
    extension="png"
else
    extension=$1
fi

./Scripts/plotResults.py --output="$plot_folder/nodes.$extension" --ylim=50 --xtics=2500 "$results_folder" nodes mauce rnd [thompsonb,mats]
./Scripts/plotResults.py --output="$plot_folder/nodesp.$extension" --ylim=270 --xtics=2500 "$results_folder" nodesp mauce --ranges=1.0 rnd [thompsonp,mats]
./Scripts/plotResults.py --output="$plot_folder/mines.$extension" --ylim=3200 "$results_folder" minesavg mauce rnd [thompsonb,mats]
./Scripts/plotResults.py --output="$plot_folder/wind.$extension" --ylim=170 "$results_folder" wind  rnd mauce [thompson,mats]
./Scripts/plotResults.py --output="$plot_folder/wind2.$extension" --ylim=10 --xlim=1000 --xtics=250 "$results_folder" wind  rnd mauce [thompson,mats]
./Scripts/plotResults.py --output="$plot_folder/sensitivity.$extension" --ylim=0:2000 --xtics=2500 --cumulative=1-na "$results_folder" nodesp mauce
