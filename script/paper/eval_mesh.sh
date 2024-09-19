#!/bin/bash

# Setting environment variable
export CUDA_VISIBLE_DEVICES="0"

# Base directory path
base_dir="/home/youngju/3d-recon/UFORecon/best_to_worst/scan106/random_trained"

# Iterate over direct child directories inside the base directory
for dir in "$base_dir"/*; do
    if [ -d "$dir" ]; then  # Check if it's a directory
        echo "Processing directory: $dir"

        # Executing Python script with specified arguments for each directory
        python evaluation/dtu_eval.py \
        --dataset_dir "/home/youngju/3d-recon/datasets/SampleSet" \
        --outdir "$dir" \
        --mode "mesh" \
        --vis_out_dir "$dir/vis"
    fi
done