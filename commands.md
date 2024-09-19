 python3 -m src.main +experiment=dtu data_loader.train.batch_size=1 dataset.view_sampler.num_context_views=2 wandb.mode=online dataset.view_selection_type=random model.encoder.pred_campose=false dataset.single_view=false model.encoder.predict_only_canonical=false


  python3 -m src.main +experiment=re10k \
    wandb.mode=online \ 
    data_loader.train.batch_size=1 \
    dataset.view_sampler.num_context_views=2 \
    model.encoder.pred_campose=false \
    dataset.single_view=false \
    model.encoder.predict_only_canonical=false
