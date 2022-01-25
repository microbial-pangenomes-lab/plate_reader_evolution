#!/bin/bash
set -eo pipefail

mkdir -p out

indir=$1

for folder in $(find $indir -maxdepth 1 -type d -name 'EXP*Evol*');
do
  echo $folder;exp=$(basename $folder | awk -F '_' '{print $1}');
  mkdir -p out/$exp/;
  python3 parse_folder-runner.py $folder $indir/Plate\ Design\ Evol\ \(Vertical\).xlsx out/$exp/$exp"_evol.tsv";
  mkdir -p out/$exp/plate_plots;
  mkdir -p out/$exp/plate_plots/evol;
  python3 plot_plate-runner.py out/$exp/$exp"_evol.tsv" out/$exp/plate_plots/evol;
  mkdir -p out/$exp/evol_plots/;
  python3 plot_evol-runner.py out/$exp/$exp"_evol.tsv" out/$exp/evol_plots/;
done

for folder in $(find $indir -maxdepth 1 -type d -name 'EXP*MIC*');
do
  echo $folder;exp=$(basename $folder | awk -F '_' '{print $1}');
  mkdir -p out/$exp/;
  python3 parse_folder-runner.py --mic $folder $indir/Plate\ Design\ MIC\ \(Vertical\).xlsx out/$exp/$exp"_mic.tsv";
  mkdir -p out/$exp/plate_plots;
  mkdir -p out/$exp/plate_plots/mic;
  python3 plot_plate-runner.py out/$exp/$exp"_mic.tsv" out/$exp/plate_plots/mic;
  mkdir -p out/$exp/mic_plots/;
  python3 compute_mic-runner.py out/$exp/$exp"_mic.tsv" out/$exp/MICs.tsv --plot --plots-output out/$exp/mic_plots/;
done
