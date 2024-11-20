#!/usr/bin/env bash

ROOT_DIR="/home/lucy/ssd/Codes/mvsplat/outputs/test/dtu"
# ROOT_DIR=$1
# voxel_size matters: 1.5 in DTU dataset, 0.005 in BlendedMVS dataset
python tsdf_fusion.py --n_view 3 --voxel_size 1.5 --test_view 23 24 33 --dataset DTU --root_dir=$ROOT_DIR 