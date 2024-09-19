#!/bin/bash

# Setting environment variable
export CUDA_VISIBLE_DEVICES="0"

# Base directory path
base_dir="/home/youngju/3d-recon/UFORecon/best_to_worst/scan65/best_trained"

# Iterate over direct child directories inside the base directory
for dir in "$base_dir"/*; do
    if [ -d "$dir" ]; then  # Check if it's a directory

        echo "Processing directory: $dir"

        # Extract view pairs from the directory name
        # Format assumed: 13_15_42_best_to_worst => Extract 13, 15, 42
        DIR_NAME=$(basename "$dir")
        IFS='_' read -ra ADDR <<< "$DIR_NAME"

        # Assign values from the array (assuming they are at fixed positions)
        PAIR1=${ADDR[0]}
        PAIR2=${ADDR[1]}
        PAIR3=${ADDR[2]}

        echo "PAIR1: $PAIR1"
        echo "PAIR2: $PAIR2"
        echo "PAIR3: $PAIR3"

        # Construct view pair string
        VIEW_PAIR="${PAIR1} ${PAIR2} ${PAIR3}"

        # Executing Python script with specified arguments for each directory
        python evaluation/clean_mesh.py \
        --root_dir "/home/youngju/3d-recon/datasets/DTU_TEST" \
        --out_dir "${dir}/mesh" \
        --view_pair $PAIR1 $PAIR2 $PAIR3
    fi
done