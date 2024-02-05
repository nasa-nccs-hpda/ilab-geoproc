#!/bin/bash

# This script setups the files to run gen_vrt.py across multiple
# nodes through pdsh. There has to be a more bash agnostic way
# of doing this, but this is a 5 minutes effort to get it done

# generate list of nodes to parallelize across
ilab_hosts=()
for i in {201..212}; do
    ilab_hosts+=("ilab${i}")
done

forest_hosts=()
for i in {201..210}; do
    forest_hosts+=("forest${i}")
done

all_hosts+=( "${ilab_hosts[@]}" "${forest_hosts[@]}" )
echo "${all_hosts[@]}"

# Generate full vrt list based on init and end intervals
# TODO: make these intervals part of the arguments from 
# the script in question, same with the output path
seq 392 1012 > Collection2_vrt_requests/GLAD_ARD_Intervals_ALL.csv

# Generate splitted files based on number of hosts and list of intervals
# TODO: calculate split value on the fly to avoid having to manually set
# the files per split
split -l 29 Collection2_vrt_requests/GLAD_ARD_Intervals_ALL.csv Collection2_vrt_requests/GLAD_ARD_Tiles_ABoVE_

# Rename the output tiles based on the host used for this run
counter=0
for filename in `ls Collection2_vrt_requests/GLAD_ARD_Tiles_ABoVE_*`; do
    echo $filename ${all_hosts[$counter]} "${filename%_*}_${all_hosts[$counter]}"
    mv $filename "${filename%_*}_${all_hosts[$counter]}"
    counter=$(( counter + 1 ))
done
