python3 -m src.main +experiment=dtu data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 wandb.mode=online dataset.view_selection_type=random model.encoder.pred_campose=false dataset.single_view=false model.encoder.predict_only_canonical=false


python3 -m src.main +experiment=dtu wandb.mode=online data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 model.encoder.pred_campose=false dataset.single_view=false model.encoder.predict_only_canonical=false


###################################### Small baseline ###################################################################################################
###################################### Small baseline ###################################################################################################
###################################### Small baseline ###################################################################################################

# 3 views gt pose
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/small-baseline/mvsplat-3views-dtu-gtpose/23_24_33-22_15_34

# 3 views Noise 0.01
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/small-baseline/mvsplat-3views-dtu-noise-001/23_24_33-22_15_34 test.noisy_pose=true test.noisy_level=0.01

# 3 views Noise 0.03
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/small-baseline/mvsplat-3views-dtu-noise-003/23_24_33-22_15_34 test.noisy_pose=true test.noisy_level=0.03

# 3 views Noise 0.05
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/small-baseline/mvsplat-3views-dtu-noise-005/23_24_33-22_15_34 test.noisy_pose=true test.noisy_level=0.05

# 3 views Noise 0.15
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/small-baseline/mvsplat-3views-dtu-noise-015/23_24_33-22_15_34 test.noisy_pose=true test.noisy_level=0.15

###################################### Large baseline ###################################################################################################
###################################### Large baseline ###################################################################################################
###################################### Large baseline ###################################################################################################

# 3 views gt pose
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[34,14,32] dataset.test_target_views=[23,42,16] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/large-baseline/mvsplat-3views-dtu-gtpose/34_14_32-23_42_16

# 3 views Noise 0.01
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[34,14,32] dataset.test_target_views=[23,42,16] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/large-baseline/mvsplat-3views-dtu-noise-001/34_14_32-23_42_16 test.noisy_pose=true test.noisy_level=0.01

# 3 views Noise 0.03
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[34,14,32] dataset.test_target_views=[23,42,16] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/large-baseline/mvsplat-3views-dtu-noise-003/34_14_32-23_42_16 test.noisy_pose=true test.noisy_level=0.03

# 3 views Noise 0.05
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[34,14,32] dataset.test_target_views=[23,42,16] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/large-baseline/mvsplat-3views-dtu-noise-005/34_14_32-23_42_16 test.noisy_pose=true test.noisy_level=0.05

# 3 views Noise 0.15
python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[23,24,33] dataset.test_target_views=[22,15,34] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/dtu/005_depth test.noisy_pose=true test.noisy_level=0.05

 python -m src.main +experiment=re10k wandb.mode=disabled mode=test test.compute_scores=true dataset/view_sampler=evaluation data_loader.train.batch_size=1 checkpointing.load=checkpoints/mvsplat_re10k.ckpt test.output_path=./test/re10k/005_depth test.noisy_pose=true test.noisy_level=0.05

 python -m src.main +experiment=dtu wandb.mode=disabled mode=test data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=3 dataset.view_selection_type=random dataset.test_context_views=[34,14,32] dataset.test_target_views=[23,42,16] checkpointing.load=/home/lucy/ssd/Codes/mvsplat-baseline/outputs/mvsplat-baseline/checkpoints/mvsplat_dtu_140k.ckpt test.output_path=./test/dtu/005_large test.noisy_pose=true test.noisy_level=0.05