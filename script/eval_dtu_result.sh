#!/usr/bin/env bash
export CUDA_VISIBLE_DEVICES="0"

DATASET="/home/youngju/3d-recon/datasets/SampleSet" ##set to your SampleSet_MVS_Data
OUT_DIR='/home/youngju/3d-recon/UFORecon/checkpoints_n_views/outputs_23_34'
python evaluation/dtu_eval.py --dataset_dir $DATASET $@ --outdir $OUT_DIR $@


python test_examples/log_to_csv.py --log_file_path $OUT_DIR/eval_final.log --csv_output_path $OUT_DIR/out.csv