PAIRS_FILE="/home/youngju/3d-recon/UFORecon/script/paper/scan65_level135.txt"

# Read each line from the file
while IFS= read -r line; do
    # Remove brackets and trailing comma, then split into an array
    line=${line//[\[\],]/}
    read -ra PAIRS <<< "$line"

    # Assign values from the array
    PAIR1=${PAIRS[0]}
    PAIR2=${PAIRS[1]}
    PAIR3=${PAIRS[2]}

    # Concatenate PAIR values with underscores for INPUT_PAIR
    INPUT_PAIR="${PAIR1}_${PAIR2}_${PAIR3}"

    # Using PAIR values directly for TEXT
    TEXT="${PAIR1} ${PAIR2} ${PAIR3}"

    echo "INPUT_PAIR: $INPUT_PAIR"

    # Executing the Python script with the generated arguments
    CUDA_VISIBLE_DEVICES=0 python /home/youngju/3d-recon/UFORecon/main.py \
    --extract_geometry \
    --set 0 \
    --stage 0 \
    --test_n_view 3 \
    --test_ray_num 800 \
    --volume_type transmvsnet \
    --volume_reso 96 \
    --depth_pos_encoding \
    --feature_extractor transmvsnet \
    --explicit_similarity \
    --mvs_depth_guide 1 \
    --test_dir /home/youngju/3d-recon/datasets/DTU_TEST \
    --load_ckpt /home/youngju/3d-recon/UFORecon/pretrained/uforecon_random_ep9.ckpt \
    --out_dir /home/youngju/3d-recon/UFORecon/best_to_worst/scan65/random_trained/${INPUT_PAIR}_best_to_worst \
    --test_ref_view $TEXT

done < "$PAIRS_FILE"