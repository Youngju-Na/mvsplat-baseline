#!/bin/bash

# Fixed reference view
fixed_view=23

# List of other views to pair with the fixed reference view
views=(24 22 15 34 14 32 16 35 25)

# Base command parts that do not change
base_command="python -m src.main \
  +experiment=dtu \
  data_loader.train.num_workers=0 \
  data_loader.test.num_workers=0 \
  data_loader.val.num_workers=0 \
  checkpointing.load=/home/lucy/ssd/Codes/mvsplat/checkpoints/epoch_24-step_300000-scaled.ckpt \
  test.output_path=test/mvsplat-randomset/ \
  mode=test \
  model.encoder.pred_campose=false \
  +experiment.dataset.image_shape=[224,224] \
  dataset/view_sampler=evaluation \
  test.compute_scores=true \
  dataset.view_sampler.num_context_views=2 \
  dataset.single_view=false"

# Loop over each view to pair with the fixed view
for view in "${views[@]}"; do
    if [[ $view -ne $fixed_view ]]; then
        # Set the specific view pair and output path for this iteration
        test_ref_views="dataset.test_ref_views=[$fixed_view,$view]"
        output_path="test.output_path=test/mvsplat-best-set/$fixed_view-$view"

        # Construct and run the full command
        full_command="$base_command $test_ref_views $output_path"
        echo "Running command with views $fixed_view and $view"
        eval $full_command
    fi
done